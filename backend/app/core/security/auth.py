"""Authentication primitives: password hashing and JWT lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(
    subject: str,
    tenant_id: str,
    roles: list[str],
    extra: dict | None = None,
) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "roles": roles,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "iss": settings.app_name,
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, tenant_id: str) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_ttl_days),
        "iss": settings.app_name,
        "typ": "refresh",
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on any failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])