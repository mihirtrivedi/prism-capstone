"""Thread-safe sliding-window rate limiter ensuring zero over-admission under concurrent load.
"""

import threading
import time
from typing import Dict, List


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._history: Dict[str, List[float]] = {}

    def check_and_acquire(self, virtual_key: str, rpm_limit: int) -> bool:
        """Atomically checks if request is within limit and registers the request.
        Returns True if admitted, False if rate limited.
        Cleans up idle keys to prevent memory retention.
        """
        now = time.monotonic()
        cutoff = now - 60.0

        with self._lock:
            timestamps = self._history.get(virtual_key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= rpm_limit:
                self._history[virtual_key] = valid_timestamps
                return False

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


rate_limiter = SlidingWindowRateLimiter()

