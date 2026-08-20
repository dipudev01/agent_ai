"""Health and readiness endpoints for liveness/readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    # Production: probe DB, Redis, and Kafka connectivity here.
    return {"status": "ready"}