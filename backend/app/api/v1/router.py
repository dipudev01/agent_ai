from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import agents, auth, chats, documents, health, tenants

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chats.router)
api_router.include_router(agents.router)
api_router.include_router(tenants.router)
api_router.include_router(documents.router)