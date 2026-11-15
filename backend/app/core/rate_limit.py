import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AppError


class RateLimitExceeded(AppError):
    status_code = 429
    code = "rate_limited"


class SlidingWindowLimiter:
    """Basic in-memory per-IP limiter. Fine for a single process; use Redis if you ever scale out."""

    def __init__(self):
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window: float = 60.0) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            raise RateLimitExceeded("Too many requests, please slow down and try again shortly")
        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


limiter = SlidingWindowLimiter()


def rate_limit(name: str, setting: str) -> Callable:
    """Dependency factory: limit read from settings at request time so it stays configurable."""

    def _dep(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        limiter.check(f"{name}:{ip}", getattr(get_settings(), setting))

    return _dep
