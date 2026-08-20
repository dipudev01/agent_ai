"""Per-endpoint distributed rate limiting backed by Redis."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float, redis_client=None) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.redis = redis_client
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
        client = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        client = client or (request.client.host if request.client else "unknown")
        key = f"{tenant}:{user}:{client}:{request.url.path}"
        allowed = await self._consume_distributed(key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded", "code": "rate_limited"},
                headers={"Retry-After": "1"},
            )
        return await call_next(request)

    async def _consume_distributed(self, key: str) -> bool:
        if self.redis is not None:
            redis_key = f"bfsi:rate:{key}"
            try:
                count = await self.redis.incr(redis_key)
                if count == 1:
                    await self.redis.expire(redis_key, 60)
                return count <= self.capacity
            except Exception:
                if settings.is_production:
                    return False
        return self._consume(key)


default_limiter = RateLimiter(capacity=60, refill_per_sec=10)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter = default_limiter) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        return await self.limiter.enforce(request, call_next)
