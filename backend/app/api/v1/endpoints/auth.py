"""Authentication endpoints: login (password), refresh. OIDC/SAML identity
provider integration plugs in behind the same token contract."""

from __future__ import annotations

import hashlib
from typing import TypedDict

from fastapi import APIRouter, HTTPException

from app.api.v1.schemas import LoginRequest, LoginResponse
from app.core.config import settings
from app.core.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.audit import record

router = APIRouter(prefix="/auth", tags=["auth"])


class _DemoUser(TypedDict):
    tenant_id: str
    roles: list[str]
    password: str


# Demo users seeded for local development only.
_DEMO_USERS: dict[str, _DemoUser] = {
    "customer@demo.com": {
        "tenant_id": "t_axisdemo",
        "roles": ["customer"],
        "password": hash_password("demo1234"),
    },
    "officer@demo.com": {
        "tenant_id": "t_axisdemo",
        "roles": ["loan_officer", "compliance_officer"],
        "password": hash_password("demo1234"),
    },
}


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    demo = _DEMO_USERS.get(body.email.lower())
    if demo is None or not verify_password(body.password, demo["password"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    user_id = f"user_{hashlib.md5(body.email.encode()).hexdigest()[:8]}"
    await record(
        tenant_id=demo["tenant_id"],
        correlation_id="login",
        actor_type="user",
        actor_id=user_id,
        action="auth.login",
        resource_type="session",
        resource_id=user_id,
        outcome="success",
    )
    return LoginResponse(
        access_token=create_access_token(user_id, demo["tenant_id"], demo["roles"]),
        refresh_token=create_refresh_token(user_id, demo["tenant_id"]),
        user_id=user_id,
        tenant_id=demo["tenant_id"],
        roles=demo["roles"],
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.post("/refresh")
async def refresh(refresh_token: str) -> dict:
    try:
        claims = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid refresh token") from exc
    if claims.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="not a refresh token")
    return {
        "access_token": create_access_token(
            claims["sub"], claims["tenant_id"], claims.get("roles", [])
        )
    }