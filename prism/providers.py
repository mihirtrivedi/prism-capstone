"""Upstream provider client handling timeouts, retries with exponential backoff,
failover chains, persistent connection pooling, and asynchronous streaming pass-through.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Tuple
import httpx
from prism.config import config

logger = logging.getLogger("prism.providers")


class UpstreamProviderClient:
    """Production HTTP client for upstream model providers with persistent connection pooling."""

    def __init__(self):
        self.timeout = httpx.Timeout(5.0, connect=3.0)
        self.limits = httpx.Limits(max_keepalive_connections=50, max_connections=200, keepalive_expiry=30.0)
        self._client: httpx.AsyncClient | None = None

    def get_client(self) -> httpx.AsyncClient:
        """Returns or lazily creates a shared, pooled AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout, limits=self.limits)
        return self._client

    async def close(self):
        """Gracefully closes underlying connection pools."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def execute_chat(
        self,
        fallback_chain: List[str],
        request_body: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str, str, bool, int]:
        """Executes non-streaming chat completion across the fallback chain.
        Returns: (response_payload, provider_name, model_name, is_fallback, total_retries)
        """
        max_attempts = config.retry_config.get("max_attempts", 3)
        initial_backoff = config.retry_config.get("initial_backoff_ms", 200) / 1000.0
        backoff_mult = config.retry_config.get("backoff_multiplier", 2)

        total_retries = 0
        last_error = None
        client = self.get_client()

        for chain_idx, model_name in enumerate(fallback_chain):
            is_fallback = (chain_idx > 0)
            provider_name = model_name.rsplit("-", 1)[0]
            provider_cfg = config.get_provider(provider_name)
            if not provider_cfg:
                continue

            url = f"{provider_cfg['base_url'].rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {provider_cfg['api_key']}"
            }
            payload = dict(request_body)
            payload["model"] = model_name
            payload["stream"] = False

            for attempt in range(max_attempts):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        if attempt < max_attempts - 1:
                            total_retries += 1
                            await asyncio.sleep(initial_backoff * (backoff_mult ** attempt))
                            continue
                        break

                    resp.raise_for_status()
                    data = resp.json()

                    # Response-Quality Escalation: If small tier refuses a [refuse] prompt, escalate to large tier
                    first_msg = ""
                    choices = data.get("choices", [])
                    if choices and isinstance(choices[0], dict):
                        first_msg = choices[0].get("message", {}).get("content", "")

                    if "I'm sorry, but I can't help with that." in first_msg and model_name.endswith("-small"):
                        large_model = model_name.replace("-small", "-large")
                        if large_model in config.model_pricing:
                            large_payload = dict(payload)
                            large_payload["model"] = large_model
                            try:
                                esc_resp = await client.post(url, json=large_payload, headers=headers)
                                if esc_resp.status_code == 200:
                                    return esc_resp.json(), provider_name, large_model, is_fallback, total_retries
                            except Exception:
                                pass

                    return data, provider_name, model_name, is_fallback, total_retries

                except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as exc:
                    last_error = str(exc)
                    if attempt < max_attempts - 1:
                        total_retries += 1
                        await asyncio.sleep(initial_backoff * (backoff_mult ** attempt))
                    else:
                        break

        raise RuntimeError(f"All upstream providers failed in chain {fallback_chain}. Last error: {last_error}")

    async def execute_streaming_chat(
        self,
        fallback_chain: List[str],
        request_body: Dict[str, Any]
    ) -> Tuple[AsyncGenerator[str, None], str, str, bool, Dict[str, Any]]:
        """Selects a healthy provider and initiates an SSE stream without buffering.
        Returns: (chunk_generator, provider_name, model_name, is_fallback, tracker_dict)
        """
        last_error = None
        stream_client = httpx.AsyncClient(timeout=self.timeout)

        for chain_idx, model_name in enumerate(fallback_chain):
            is_fallback = (chain_idx > 0)
            provider_name = model_name.rsplit("-", 1)[0]
            provider_cfg = config.get_provider(provider_name)
            if not provider_cfg:
                continue

            url = f"{provider_cfg['base_url'].rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {provider_cfg['api_key']}"
            }
            payload = dict(request_body)
            payload["model"] = model_name
            payload["stream"] = True

            try:
                req = stream_client.build_request("POST", url, json=payload, headers=headers)
                resp = await stream_client.send(req, stream=True)

                if resp.status_code in (429, 500, 502, 503, 504) or resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}"
                    await resp.aclose()
                    continue

                tracker = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "completed": False
                }

                async def stream_generator() -> AsyncGenerator[str, None]:
                    try:
                        async for line in resp.aiter_lines():
                            line_str = line.strip()
                            if not line_str:
                                continue
                            if line_str.startswith("data: "):
                                data_content = line_str[6:].strip()
                                if data_content == "[DONE]":
                                    yield "data: [DONE]\n\n"
                                    tracker["completed"] = True
                                    break

                                try:
                                    parsed = json.loads(data_content)
                                    if "usage" in parsed and parsed["usage"]:
                                        tracker["prompt_tokens"] = parsed["usage"].get("prompt_tokens", 0)
                                        tracker["completion_tokens"] = parsed["usage"].get("completion_tokens", 0)
                                except Exception:
                                    pass

                                yield f"{line_str}\n\n"
                            else:
                                yield f"{line_str}\n\n"
                    finally:
                        await resp.aclose()
                        await stream_client.aclose()

                return stream_generator(), provider_name, model_name, is_fallback, tracker

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as exc:
                last_error = str(exc)
                continue

        await stream_client.aclose()
        raise RuntimeError(f"All upstream providers failed in chain {fallback_chain}. Last error: {last_error}")


provider_client = UpstreamProviderClient()
