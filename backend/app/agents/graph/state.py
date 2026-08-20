"""State schema for the LangGraph agent orchestration.

The state mirrors the data an agent loop carries across steps: the message
conversation, the tools invoked so far, tool outputs, the running step count,
and the final reply. Reducers (Annotated[..., add]) accumulate across node
executions so LangGraph merges contributions from multiple nodes/cycles.
"""

from __future__ import annotations

from datetime import datetime
from operator import add
from typing import Annotated, Any, TypedDict

from app.agents.base import AgentInput


class AgentGraphState(TypedDict, total=False):
    """Checkpointable state threaded through the LangGraph agent graph.

    Security note: the state NEVER carries raw PII beyond what the underlying
    guardrails and tool authorization already permit. Tenant and user identity
    live on the AgentInput context, not inside the graph state.
    """

    messages: Annotated[list[dict[str, Any]], add]
    used_tools: Annotated[list[str], add]
    tool_outputs: Annotated[list[dict[str, Any]], add]
    steps: int
    reply: str
    token_usage: dict[str, int]
    needs_human_approval: bool
    decision: dict[str, Any] | None
    error: str | None
    pending_tool_calls: list[dict[str, Any]]
    started_at: datetime
    duration_ms: int
    _input: AgentInput
    # supervisor delegation fields
    specialist_key: str
    delegated_to: list[str]
    specialist_reply: str
    specialist_tools: list[str]
    specialist_outputs: list[dict[str, Any]]