"""Chat endpoint — the primary customer/agent conversation interface.

Flow: authenticate → authorize → rate limit → route → agent gateway (guardrails)
→ tool authorization → deterministic decisioning where applicable → audit.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies import PrincipalDep
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.services.agent_service import AgentExecutionError, run_agent_for_user

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    principal: PrincipalDep,
):
    conversation_id = body.conversation_id or str(uuid.uuid4())
    correlation = request.headers.get(settings.correlation_header) or str(uuid.uuid4())
    try:
        result = await run_agent_for_user(
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            roles=principal.roles,
            correlation_id=correlation,
            message=body.message,
            conversation_id=conversation_id,
            agent_hint=body.agent_hint,
            resource_owner_id=principal.user_id if not principal.is_staff else None,
        )
    except AgentExecutionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return ChatResponse(
        conversation_id=conversation_id,
        agent=result["agent"],
        reply=result["reply"],
        used_tools=result["used_tools"],
        delegated_to=result["delegated_to"],
        needs_human_approval=result["needs_human_approval"],
        decision=result["decision"],
        duration_ms=result["duration_ms"],
    )