"""Agent registry discovery endpoints (for consoles and observability)."""

from __future__ import annotations

from fastapi import APIRouter

from app.agents.registry import list_agents
from app.api.dependencies import PrincipalDep
from app.api.v1.schemas import AgentListResponse, AgentSpec, ToolSpecResponse
from app.tools.registry import list_specs

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List available agents",
    description="Lists agents available to the authenticated tenant and console.",
)
async def list_all_agents(principal: PrincipalDep):
    specs = [AgentSpec(**s) for s in list_agents().values()]
    return AgentListResponse(agents=specs)


@router.get(
    "/tools",
    response_model=list[ToolSpecResponse],
    summary="List registered tools",
    description="Lists tools registered with the platform tool registry.",
)
async def list_registered_tools(principal: PrincipalDep):
    return [ToolSpecResponse(name=t.name, description=t.description) for t in list_specs()]
