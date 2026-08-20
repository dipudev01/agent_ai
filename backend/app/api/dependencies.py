"""Shared FastAPI dependencies: authentication, tenant context, permissions."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError

from app.core.security.auth import decode_token
from app.core.security.rbac import default_rbac


class Principal:
    def __init__(self, sub: str, tenant_id: str, roles: list[str]) -> None:
        self.user_id = sub
        self.tenant_id = tenant_id
        self.roles = roles

    @property
    def is_staff(self) -> bool:
        return bool(set(self.roles) & {"institution_admin", "compliance_officer", "fraud_analyst", "loan_officer"})


def get_principal(request: Request) -> Principal:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        claims = decode_token(auth.removeprefix("Bearer "))
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    return Principal(
        sub=claims.get("sub", ""),
        tenant_id=claims.get("tenant_id", ""),
        roles=claims.get("roles", []),
    )


def require_permission(permission: str):
    def dep(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        rbac = default_rbac()
        if not any(rbac.can(role, permission) for role in principal.roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="insufficient permissions")
        return principal

    return dep


PrincipalDep = Annotated[Principal, Depends(get_principal)]
CorrelationIdDep = Annotated[str | None, Header(alias="X-Correlation-ID")]