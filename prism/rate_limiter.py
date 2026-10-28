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
        """
        now = time.monotonic()
        cutoff = now - 60.0

        with self._lock:
            if virtual_key not in self._history:
                self._history[virtual_key] = []

            # Clean entries older than 60 seconds
            timestamps = self._history[virtual_key]
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._history[virtual_key] = valid_timestamps

            if len(valid_timestamps) >= rpm_limit:
                return False

            self._history[virtual_key].append(now)
            return True


rate_limiter = SlidingWindowRateLimiter()

