"""Health and readiness endpoints for liveness/readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.v1.schemas import HealthResponse
from app.core.container import container

router = APIRouter(tags=["health"])


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Check liveness",
    description="Returns 200 when the API process is alive.",
)
async def live() -> HealthResponse:
    return {"status": "ok"}


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Check readiness",
    description="Returns 200 when the API is ready to receive traffic.",
)
async def ready() -> HealthResponse:
    checks = await container.readiness()
    if not all(checks.values()):
        return JSONResponse(status_code=503, content={"status": "not_ready", "checks": checks})
    return {"status": "ready"}
