"""In-memory sliding-window rate limiter (SEC-11). One uvicorn worker (A-13), so a dict of deques is enough.

ponytail: process-local state; use a shared store (Redis) if the API ever runs with more than one worker.
"""
import threading
import time
from collections import defaultdict, deque

from app.core.errors import ApiError


class RateLimiter:
    def __init__(self, limit: int, window_s: float) -> None:
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        """Record a hit for `key`, or raise 429 RATE_LIMITED with Retry-After."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window_s:
                hits.popleft()
            if len(hits) >= self.limit:
                retry_after = max(1, int(self.window_s - (now - hits[0])) + 1)
                raise ApiError(
                    "RATE_LIMITED", 429, "Too many requests. Please wait and try again.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
