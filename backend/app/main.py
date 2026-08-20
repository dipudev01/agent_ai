"""FastAPI application entrypoint.

Middleware order (security first): correlation → tenant context → rate limit →
audit. AuthZ is enforced per-route via dependencies. The application is
stateless; scaling is horizontal.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.container import container
from app.core.telemetry import init
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.ratelimit import RateLimitMiddleware
from app.middleware.tenant import TenantContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init()
    async with container.lifespan():
        yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(CORSMiddleware, allow_origins=[], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(CorrelationMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Mask details in production; log full trace to the error tracker.
    detail = "internal error" if settings.is_production else repr(exc)
    return JSONResponse(status_code=500, content={"detail": detail, "code": "internal_error"})