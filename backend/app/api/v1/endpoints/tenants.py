"""Tenant admin endpoints: create tenants, institutions, users. Platform admin only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.dependencies import Principal, PrincipalDep, require_permission
from app.api.v1.schemas import InstitutionCreatedResponse, TenantCreatedResponse, UserCreatedResponse
from app.core.security.auth import hash_password
from app.db.models.tenant import Institution, Tenant
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.audit import record

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post(
    "",
    status_code=201,
    response_model=TenantCreatedResponse,
    summary="Create a tenant",
    description="Creates a tenant for platform administration and returns its identifier.",
)
async def create_tenant(
    principal: Principal = Depends(require_permission("tenant:*")),
    name: str = Query(..., examples=["Axis Demo Bank"]),
    slug: str = Query(..., examples=["axis-demo-bank"]),
    data_residency: str = Query("in", examples=["in"]),
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


@router.post(
    "/{tenant_id}/users",
    status_code=201,
    response_model=UserCreatedResponse,
    summary="Create a tenant user",
    description="Creates a user within the specified tenant with the supplied roles.",
)
async def create_user(
    principal: Principal = Depends(require_permission("user:write")),
    tenant_id: str = Path(..., examples=["t_01J8TENANT"]),
    email: str = Query(..., examples=["user@example.com"]),
    full_name: str = Query(..., examples=["Asha Mehta"]),
    password: str = Query(..., examples=["StrongPassword123!"], min_length=8),
    roles: list[str] = Query(..., examples=[["customer"]]),
):
    if tenant_id != principal.tenant_id and "platform_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="tenant access denied")
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


@router.post(
    "/{tenant_id}/institutions",
    status_code=201,
    response_model=InstitutionCreatedResponse,
    summary="Create an institution",
    description="Creates an institution under the specified tenant.",
)
async def create_institution(
    principal: PrincipalDep,
    tenant_id: str = Path(..., examples=["t_01J8TENANT"]),
    name: str = Query(..., examples=["Axis Demo Bank"]),
    code: str = Query(..., examples=["AXIS-DEMO"]),
):
    async with SessionLocal() as session:
        inst = Institution(tenant_id=tenant_id, name=name, code=code)
        session.add(inst)
        await session.commit()
        return {"institution_id": inst.id, "tenant_id": tenant_id}
