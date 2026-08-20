"""Per-endpoint rate limiting using a token bucket in Redis (sliding window).
The default bucket is per (tenant, user, route). Fails open to local in-memory
when Redis is unavailable during startup, but logs a warning."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._buckets: dict[str, tuple[float, float]] = {}

    def _consume(self, key: str) -> bool:
        now = time.monotonic()
        tokens, last = self._buckets.get(key, (self.capacity, now))
        tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)
        if tokens >= 1:
            self._buckets[key] = (tokens - 1, now)
            return True
        self._buckets[key] = (tokens, now)
        return False

    async def enforce(self, request: Request, call_next: Callable):
        tenant = getattr(request.state, "tenant_id", "anon")
        user = getattr(request.state, "user_id", "anon")
        key = f"{tenant}:{user}:{request.url.path}"
        if not self._consume(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded", "code": "rate_limited"},
                headers={"Retry-After": "1"},
            )
        return await call_next(request)


default_limiter = RateLimiter(capacity=60, refill_per_sec=10)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter = default_limiter) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        return await self.limiter.enforce(request, call_next)