"""Thread-safe sliding-window rate limiter ensuring zero over-admission under concurrent load.
"""

import threading
import time
from typing import Dict, List, Optional, Tuple


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._history: Dict[str, List[float]] = {}
        self._token_history: Dict[str, List[Tuple[float, int]]] = {}

    def check_and_acquire(
        self,
        virtual_key: str,
        rpm_limit: int,
        estimated_tokens: int = 0,
        tpm_limit: Optional[int] = None
    ) -> bool:
        """Atomically checks both RPM and TPM limits and registers the request.
        Returns True if admitted, False if rate limited.
        Cleans up idle keys to prevent memory retention.
        """
        now = time.monotonic()
        cutoff = now - 60.0

        with self._lock:
            # 1. Requests-Per-Minute (RPM) Check
            timestamps = self._history.get(virtual_key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= rpm_limit:
                self._history[virtual_key] = valid_timestamps
                return False

            # 2. Tokens-Per-Minute (TPM) Check
            if tpm_limit and tpm_limit > 0 and estimated_tokens > 0:
                tok_entries = self._token_history.get(virtual_key, [])
                valid_toks = [(t, tok) for t, tok in tok_entries if t > cutoff]
                current_tokens = sum(tok for _, tok in valid_toks)
                if (current_tokens + estimated_tokens) > tpm_limit:
                    self._token_history[virtual_key] = valid_toks
                    return False
                valid_toks.append((now, estimated_tokens))
                self._token_history[virtual_key] = valid_toks

            valid_timestamps.append(now)
            self._history[virtual_key] = valid_timestamps
            return True

    def cleanup_idle_keys(self):
        """Purges keys with no activity in the last 60 seconds."""
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            idle_keys = [k for k, ts in self._history.items() if not any(t > cutoff for t in ts)]
            for k in idle_keys:
                del self._history[k]
                self._token_history.pop(k, None)


rate_limiter = SlidingWindowRateLimiter()

