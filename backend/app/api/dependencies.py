"""Shared FastAPI dependencies: authentication, tenant context, permissions."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="JWT access token obtained from POST /api/v1/auth/login.",
)


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> Principal:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        claims = decode_token(credentials.credentials)
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
