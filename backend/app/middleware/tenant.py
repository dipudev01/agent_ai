"""Tenant resolution middleware — extracts the tenant from the authenticated
principal (server-side), never from client input, and sets the tenant context
for the duration of the request."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security.auth import decode_token
from app.db.session import clear_tenant_context, set_tenant_context


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_tenant_context()
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                claims = decode_token(auth.removeprefix("Bearer "))
                set_tenant_context(claims.get("tenant_id", ""), claims.get("sub"))
                request.state.tenant_id = claims.get("tenant_id")
                request.state.user_id = claims.get("sub")
                request.state.roles = claims.get("roles", [])
            except Exception:
                # Let the auth dependency produce the proper 401.
                pass
        return await call_next(request)