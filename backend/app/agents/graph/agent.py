"""LangGraph-backed agent wrapper.

Implements the same ``Agent`` contract as the classic loop (input/output
guardrails, tool authorization via tools/authz.py, memory append, audited
agent-run persistence) but drives the execution through a compiled LangGraph
StateGraph with per-run checkpoints. Security properties are identical to the
classic path; the graph only changes *how* the loop is orchestrated, never
*what* is allowed to happen.

Switching between orchestration strategies is configured by
``settings.agent_orchestrator`` ("classic" | "langgraph") and resolved by
``app.agents.factory``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.base import Agent, AgentInput, AgentResult, GuardrailError
from app.agents.graph.graph import build_agent_graph
from app.agents.graph.state import AgentGraphState
from app.gateway.models import ChatMessage

_graphs: dict[str, object] = {}


def _get_graph(agent: Agent):
    """Return the compiled graph for an agent, cached per agent key."""
    graph = _graphs.get(agent.key)
    if graph is None:
        graph = build_agent_graph(agent)
        _graphs[agent.key] = graph
    return graph


class LangGraphAgent(Agent):
    """Agent wrapper that runs the underlying agent's logic as a LangGraph."""

    def __init__(self, delegate: Agent) -> None:
        self._delegate = delegate
        super().__init__(memory=delegate._memory)  # noqa: SLF001 - shared memory store

    # -- delegated spec surface (registry/discovery behave identically) --
    @property
    def key(self) -> str:  # type: ignore[override]
        return self._delegate.key

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._delegate.name

    @property
    def description(self) -> str:  # type: ignore[override]
        return self._delegate.description

    @property
    def capabilities(self) -> list[str]:  # type: ignore[override]
        return self._delegate.capabilities

    @property
    def routing_priority(self) -> int:  # type: ignore[override]
        return self._delegate.routing_priority

    @property
    def version(self) -> str:  # type: ignore[override]
        return self._delegate.version

    @property
    def needs_hitl(self) -> bool:  # type: ignore[override]
        return self._delegate.needs_hitl

    @property
    def system_prompt(self) -> str:  # type: ignore[override]
        return self._delegate.system_prompt

    def spec(self) -> dict:
        spec = self._delegate.spec()
        spec["orchestrator"] = "langgraph"
        return spec

    # -- execution -- 
    def _available_tools(self) -> list:
        return self._delegate._available_tools()  # noqa: SLF001

    @property
    def _json_output(self) -> bool:
        return self._delegate._json_output  # type: ignore[attr-defined]

    def _guard_input(self, inp: AgentInput) -> None:
        # Delegate guardrails to the wrapped agent (identical rules).
        return self._delegate._guard_input(inp)  # noqa: SLF001

    def _guard_output(self, text: str) -> None:
        return self._delegate._guard_output(text)  # noqa: SLF001

    async def _call_llm(self, request):
        return await self._delegate._call_llm(request)  # noqa: SLF001

    def _record_tokens(self, usage: dict) -> None:
        self._delegate._record_tokens(usage)  # noqa: SLF001
        self._last_usage = usage

    async def _persist_run(self, inp, tools, outputs, reply, start) -> None:
        await self._delegate._persist_run(inp, tools, outputs, reply, start)  # noqa: SLF001

    async def invoke(self, inp: AgentInput) -> AgentResult:
        start = datetime.now(UTC)
        history = await self._memory.get_short_term(inp.conversation_id, inp.tenant_id, inp.user_id)
        messages = [ChatMessage(role="system", content=self.system_prompt).model_dump()]
        messages.extend(m.model_dump() for m in history)
        messages.append(ChatMessage(role="user", content=inp.message).model_dump())

        initial: AgentGraphState = {
            "messages": messages,
            "used_tools": [],
            "tool_outputs": [],
            "steps": 0,
            "reply": "",
            "token_usage": {},
            "needs_human_approval": False,
            "decision": None,
            "error": None,
            "started_at": start,
            "_input": inp,
            "delegated_to": [],
            "specialist_key": "",
            "specialist_reply": "",
            "specialist_tools": [],
            "specialist_outputs": [],
        }

        graph = _get_graph(self)
        final = await graph.ainvoke(initial, config={"configurable": {"thread_id": inp.correlation_id}})

        reply = final.get("reply", "")
        result = AgentResult(
            reply=reply,
            used_tools=final.get("used_tools", []),
            tool_outputs=final.get("tool_outputs", []),
            delegated_to=final.get("delegated_to", []),
            duration_ms=final.get("duration_ms", 0),
            token_usage=final.get("token_usage", {}),
            needs_human_approval=final.get("needs_human_approval", False),
            decision=final.get("decision"),
        )
        if not reply:
            result.reply = "I could not complete that request. Please retry or contact support."
        return result