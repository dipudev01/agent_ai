"""Correlation ID middleware — attaches/generates a correlation ID per request
and surfaces it on the response so all logs, spans, and events share it."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings

_correlation_ctx: ContextVar[str] = ContextVar("correlation_id", default="no-correlation-id")


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header = settings.correlation_header
        correlation_id = request.headers.get(header) or str(uuid.uuid4())
        token = _correlation_ctx.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            _correlation_ctx.reset(token)
        response.headers[header] = correlation_id
        return response


def current_correlation_id() -> str:
    return _correlation_ctx.get()