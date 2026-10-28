"""FastAPI application for Prism Gateway.
Exposes OpenAI-compatible POST /v1/chat/completions with full header contract,
streaming, rate limiting, budget enforcement, semantic caching, quality escalation, and ops console.
"""

import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from prism.config import config
from prism.cost_calculator import calculate_cost
from prism.database import db
from prism.rate_limiter import rate_limiter
from prism.router import resolve_model
from prism.semantic_cache import extract_prompt_from_messages, semantic_cache
from prism.providers import provider_client
from prism.console import HTML_DASHBOARD


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful lifecycle manager for background connection pools."""
    yield
    await provider_client.close()


app = FastAPI(
    title="Prism LLM Gateway",
    version="1.0.0",
    description="Production-grade AI gateway with smart difficulty routing, semantic cache, and tenant metering",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "gateway": "prism"}


@app.get("/", response_class=HTMLResponse)
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=HTML_DASHBOARD)


@app.get("/admin/cache/stats")
async def cache_stats():
    return db.get_cache_stats()


@app.get("/admin/tenants")
async def get_tenants():
    tenants = db.get_all_tenants()
    for t in tenants:
        t["current_spend"] = db.get_monthly_spend(t["virtual_key"])
    return tenants


@app.get("/admin/usage")
async def get_usage(key: str, from_date: Optional[str] = None, to_date: Optional[str] = None):
    return db.get_usage_summary(key, from_date, to_date)


@app.get("/admin/logs")
async def get_logs(key: Optional[str] = None, limit: int = 50):
    return db.get_logs(virtual_key=key, limit=limit)


@app.get("/admin/providers/health")
async def providers_health():
    """Health check endpoint for all upstream providers."""
    client = provider_client.get_client()
    results = []
    overall_ok = True
    for name, pcfg in config.providers.items():
        base = pcfg["base_url"].rstrip("/")
        health_url = base.replace("/v1", "") + "/health"
        is_healthy = False
        try:
            resp = await client.get(health_url, timeout=2.0)
            if resp.status_code == 200:
                is_healthy = True
        except Exception:
            is_healthy = False

        if not is_healthy:
            overall_ok = False
        results.append({
            "name": name,
            "status": "healthy" if is_healthy else "degraded",
            "url": health_url
        })
    return {"status": "ok" if overall_ok else "degraded", "providers": results}


@app.post("/admin/keys")
async def create_key(request: Request):
    """Creates or updates a tenant virtual key."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    team = body.get("team", "default")
    key_val = body.get("virtual_key") or f"prism-sk-{team}-{uuid.uuid4().hex[:6]}"
    budget = float(body.get("monthly_budget_usd", 50.0))
    rate_lim = body.get("rate_limit", {})
    rpm = int(rate_lim.get("requests_per_minute", 60))
    tpm = int(rate_lim.get("tokens_per_minute", 100000))
    allowlist = body.get("model_allowlist", ["fast", "smart", "auto"])
    cache_cfg = body.get("semantic_cache", {})
    cache_enabled = 1 if cache_cfg.get("enabled", True) else 0
    sim_thresh = float(cache_cfg.get("similarity_threshold", 0.85))

    now_str = datetime.now(timezone.utc).isoformat()
    with db._lock:
        with db.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO tenants (
                virtual_key, team, monthly_budget_usd, requests_per_minute,
                tokens_per_minute, model_allowlist, cache_enabled, similarity_threshold,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key_val, team, budget, rpm, tpm, json.dumps(allowlist),
                cache_enabled, sim_thresh, "active", now_str
            ))
            conn.commit()

    return {
        "virtual_key": key_val,
        "team": team,
        "monthly_budget_usd": budget,
        "requests_per_minute": rpm,
        "model_allowlist": allowlist,
        "status": "active"
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    start_time = time.monotonic()
    req_id = f"chatcmpl-{uuid.uuid4().hex}"

    # 1. Parse Request Body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "Invalid JSON body", "type": "invalid_request_error", "code": "bad_request"}}
        )

    requested_model = body.get("model")
    messages = body.get("messages", [])
    stream = bool(body.get("stream", False))

    if not requested_model:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Missing 'model' field", "type": "invalid_request_error", "code": "missing_model"}}
        )

    if not isinstance(messages, list) or len(messages) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Messages list cannot be empty", "type": "invalid_request_error", "code": "empty_messages"}}
        )

    prompt_text = extract_prompt_from_messages(messages)

    # 2. Authentication: Virtual Key Validation
    virtual_key = None
    if authorization and authorization.startswith("Bearer "):
        virtual_key = authorization[7:].strip()

    tenant = db.get_tenant(virtual_key) if virtual_key else None
    if not tenant:
        db.log_request(
            request_id=req_id,
            virtual_key=virtual_key or "anonymous",
            requested_model=requested_model,
            resolved_provider=None,
            resolved_model=None,
            status="rejected_auth",
            latency_ms=round((time.monotonic() - start_time) * 1000)
        )
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "Invalid or missing virtual API key", "type": "authentication_error", "code": "authentication_error"}}
        )

    # 3. Model Existence Check (Unknown model vs Disallowed model)
    chain, route_reason = resolve_model(requested_model, prompt_text)
    primary_model = chain[0] if chain else None
    is_known_model = (
        requested_model in config.aliases
        or requested_model in config.model_pricing
        or (primary_model is not None and primary_model in config.model_pricing)
    )

    if not is_known_model:
        db.log_request(
            request_id=req_id,
            virtual_key=virtual_key,
            requested_model=requested_model,
            resolved_provider=None,
            resolved_model=None,
            status="rejected_unknown_model",
            latency_ms=round((time.monotonic() - start_time) * 1000)
        )
        return JSONResponse(
            status_code=404,
            content={"error": {"message": f"Unknown model or alias '{requested_model}'", "type": "not_found_error", "code": "model_not_found"}}
        )

    # 4. Model Allowlist Enforcement
    is_allowed = False
    if requested_model in tenant["model_allowlist"]:
        is_allowed = True
    elif requested_model in config.model_pricing and any(a in tenant["model_allowlist"] for a in ["fast", "smart"]):
        is_allowed = True

    if not is_allowed:
        db.log_request(
            request_id=req_id,
            virtual_key=virtual_key,
            requested_model=requested_model,
            resolved_provider=None,
            resolved_model=None,
            status="rejected_allowlist",
            latency_ms=round((time.monotonic() - start_time) * 1000)
        )
        return JSONResponse(
            status_code=403,
            content={"error": {"message": f"Model '{requested_model}' not allowed under this key's allowlist", "type": "model_not_allowed", "code": "model_not_allowed"}}
        )

    # 5. Rate Limit Check (Race-Safe Sliding Window)
    rpm_limit = tenant["requests_per_minute"]
    if not rate_limiter.check_and_acquire(virtual_key, rpm_limit):
        db.log_request(
            request_id=req_id,
            virtual_key=virtual_key,
            requested_model=requested_model,
            resolved_provider=None,
            resolved_model=None,
            status="rejected_rate_limit",
            latency_ms=round((time.monotonic() - start_time) * 1000)
        )
        return JSONResponse(
            status_code=429,
            content={"error": {"message": f"Rate limit of {rpm_limit} requests/minute exceeded", "type": "rate_limit_exceeded", "code": "rate_limit_exceeded"}}
        )

    # 6. Monthly Budget Enforcement
    current_spend = db.get_monthly_spend(virtual_key)
    monthly_budget = tenant["monthly_budget_usd"]
    if current_spend >= monthly_budget:
        db.log_request(
            request_id=req_id,
            virtual_key=virtual_key,
            requested_model=requested_model,
            resolved_provider=None,
            resolved_model=None,
            status="rejected_budget",
            latency_ms=round((time.monotonic() - start_time) * 1000)
        )
        return JSONResponse(
            status_code=429,
            content={"error": {"message": f"Monthly budget of ${monthly_budget:.5f} exhausted for this key", "type": "budget_exceeded", "code": "budget_exceeded"}}
        )

    # 7. Semantic Cache Check (Scoped strictly per virtual_key)
    if tenant["cache_enabled"] and not stream:
        threshold = tenant.get("similarity_threshold", 0.85)
        is_hit, cached_response, _ = semantic_cache.check_cache(virtual_key, prompt_text, threshold)
        if is_hit and cached_response:
            latency_ms = round((time.monotonic() - start_time) * 1000)
            db.record_usage(virtual_key, prompt_tokens=0, completion_tokens=0, cost_usd=0.0, is_cache_hit=True)
            db.log_request(
                request_id=req_id,
                virtual_key=virtual_key,
                requested_model=requested_model,
                resolved_provider="cache",
                resolved_model=requested_model,
                status="ok",
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                cache_result="hit",
                fallback=False,
                route_reason=route_reason,
                latency_ms=latency_ms
            )
            return JSONResponse(
                status_code=200,
                content=cached_response,
                headers={
                    "x-prism-provider": "cache",
                    "x-prism-cache": "hit",
                    "x-prism-fallback": "false",
                    "x-prism-cost-usd": "0"
                }
            )

    # 8. Dispatch to Upstream Provider (Streaming vs Non-Streaming)
    if stream:
        try:
            stream_gen, provider_name, resolved_model, is_fallback, tracker = await provider_client.execute_streaming_chat(chain, body)

            async def event_generator():
                async for chunk in stream_gen:
                    yield chunk

                # When stream completes, meter usage and log telemetry
                latency_ms = round((time.monotonic() - start_time) * 1000)
                p_toks = tracker["prompt_tokens"]
                c_toks = tracker["completion_tokens"]
                cost = calculate_cost(resolved_model, p_toks, c_toks)
                db.record_usage(virtual_key, p_toks, c_toks, cost, is_cache_hit=False)
                db.log_request(
                    request_id=req_id,
                    virtual_key=virtual_key,
                    requested_model=requested_model,
                    resolved_provider=provider_name,
                    resolved_model=resolved_model,
                    status="ok",
                    prompt_tokens=p_toks,
                    completion_tokens=c_toks,
                    cost_usd=cost,
                    cache_result="miss",
                    fallback=is_fallback,
                    route_reason=route_reason,
                    latency_ms=latency_ms
                )

            headers = {
                "x-prism-provider": f"{provider_name}/{resolved_model}",
                "x-prism-cache": "miss",
                "x-prism-fallback": "true" if is_fallback else "false",
            }
            return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)

        except Exception as exc:
            db.log_request(
                request_id=req_id,
                virtual_key=virtual_key,
                requested_model=requested_model,
                resolved_provider=None,
                resolved_model=None,
                status="upstream_error",
                latency_ms=round((time.monotonic() - start_time) * 1000)
            )
            return JSONResponse(
                status_code=502,
                content={"error": {"message": f"Upstream error: {str(exc)}", "type": "upstream_error", "code": "upstream_error"}}
            )

    else:
        # Non-Streaming execution
        try:
            resp_payload, provider_name, resolved_model, is_fallback, retries = await provider_client.execute_chat(chain, body)
            latency_ms = round((time.monotonic() - start_time) * 1000)

            usage = resp_payload.get("usage") or {}
            p_toks = usage.get("prompt_tokens", 0)
            c_toks = usage.get("completion_tokens", 0)
            cost = calculate_cost(resolved_model, p_toks, c_toks)

            db.record_usage(virtual_key, p_toks, c_toks, cost, is_cache_hit=False)
            db.log_request(
                request_id=req_id,
                virtual_key=virtual_key,
                requested_model=requested_model,
                resolved_provider=provider_name,
                resolved_model=resolved_model,
                status="ok",
                prompt_tokens=p_toks,
                completion_tokens=c_toks,
                cost_usd=cost,
                cache_result="miss",
                fallback=is_fallback,
                route_reason=route_reason,
                retries=retries,
                latency_ms=latency_ms
            )

            if tenant["cache_enabled"]:
                semantic_cache.store_cache(virtual_key, requested_model, prompt_text, resp_payload)

            headers = {
                "x-prism-provider": f"{provider_name}/{resolved_model}",
                "x-prism-cache": "miss",
                "x-prism-fallback": "true" if is_fallback else "false",
                "x-prism-cost-usd": f"{cost:.6f}"
            }
            return JSONResponse(status_code=200, content=resp_payload, headers=headers)

        except Exception as exc:
            db.log_request(
                request_id=req_id,
                virtual_key=virtual_key,
                requested_model=requested_model,
                resolved_provider=None,
                resolved_model=None,
                status="upstream_error",
                latency_ms=round((time.monotonic() - start_time) * 1000)
            )
            return JSONResponse(
                status_code=502,
                content={"error": {"message": f"Upstream error: {str(exc)}", "type": "upstream_error", "code": "upstream_error"}}
            )
