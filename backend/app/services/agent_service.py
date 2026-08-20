"""Agent orchestration service — the application-layer entry point that routes a
user message to the right agent, runs it, and records the outcome. Used by the
chats API and consumed as a workflow step by the orchestrator."""

from __future__ import annotations

from app.agents.base import AgentInput, GuardrailError
from app.agents.registry import get_agent
from app.agents.router import route
from app.services.audit import record


class AgentExecutionError(Exception): ...


async def run_agent_for_user(
    *,
    tenant_id: str,
    user_id: str,
    roles: list[str],
    correlation_id: str,
    message: str,
    conversation_id: str | None = None,
    agent_hint: str | None = None,
    resource_owner_id: str | None = None,
) -> dict:
    agent_key = route(
        AgentInput(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles,
            correlation_id=correlation_id,
            message=message,
            conversation_id=conversation_id,
            resource_owner_id=resource_owner_id,
        ),
        hint=agent_hint,
    )
    agent = get_agent(agent_key or "supervisor")
    if agent is None:
        raise AgentExecutionError(f"agent {agent_key} not found")

    inp = AgentInput(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=roles,
        correlation_id=correlation_id,
        message=message,
        conversation_id=conversation_id,
        resource_owner_id=resource_owner_id,
    )

    try:
        result = await agent.invoke(inp)
    except GuardrailError as exc:
        await record(
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            actor_type="user",
            actor_id=user_id,
            action="agent.invoke",
            resource_type="agent",
            resource_id=agent.key,
            outcome="denied",
            detail={"reason": str(exc)},
        )
        raise AgentExecutionError(str(exc)) from exc

    await record(
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        actor_type="user",
        actor_id=user_id,
        action="agent.invoke",
        resource_type="agent",
        resource_id=agent.key,
        outcome="success",
        detail={
            "agent": agent.key,
            "used_tools": result.used_tools,
            "delegated_to": result.delegated_to,
            "needs_human_approval": result.needs_human_approval,
        },
    )

    return {
        "agent": agent.key,
        "reply": result.reply,
        "used_tools": result.used_tools,
        "delegated_to": result.delegated_to,
        "needs_human_approval": result.needs_human_approval,
        "decision": result.decision,
        "duration_ms": result.duration_ms,
        "token_usage": result.token_usage,
    }