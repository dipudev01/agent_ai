"""Tenant admin endpoints: create tenants, institutions, users. Platform admin only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import Principal, PrincipalDep, require_permission
from app.core.security.auth import hash_password
from app.db.models.tenant import Institution, Tenant
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.audit import record

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", status_code=201)
async def create_tenant(
    name: str,
    slug: str,
    data_residency: str = "in",
    principal: Principal = Depends(require_permission("tenant:*")),
):
    async with SessionLocal() as session:
        tenant = Tenant(name=name, slug=slug, data_residency=data_residency)
        session.add(tenant)
        await session.flush()
        await record(
            tenant_id=tenant.id,
            correlation_id="tenant-create",
            actor_type="user",
            actor_id=principal.user_id,
            action="tenant.create",
            resource_type="tenant",
            resource_id=tenant.id,
            outcome="success",
        )
        await session.commit()
        return {"tenant_id": tenant.id}


@router.post("/{tenant_id}/users", status_code=201)
async def create_user(
    tenant_id: str,
    email: str,
    full_name: str,
    password: str,
    roles: list[str],
    principal: PrincipalDep,
):
    async with SessionLocal() as session:
        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            roles=roles,
        )
        session.add(user)
        await session.commit()
        return {"user_id": user.id, "tenant_id": tenant_id}


@router.post("/{tenant_id}/institutions", status_code=201)
async def create_institution(
    tenant_id: str,
    name: str,
    code: str,
    principal: PrincipalDep,
):
    async with SessionLocal() as session:
        inst = Institution(tenant_id=tenant_id, name=name, code=code)
        session.add(inst)
        await session.commit()
        return {"institution_id": inst.id, "tenant_id": tenant_id}