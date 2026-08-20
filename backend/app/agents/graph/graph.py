"""Builds the LangGraph execution graphs for agent orchestration.

Two graphs model the platform's orchestration as stateful, checkpointable
StateGraphs without weakening the deterministic core:

  * ``build_tool_graph`` — the generic specialist loop (LLM call -> tool
    execution -> decide), replicating ``Agent.invoke`` semantics.
  * ``build_supervisor_graph`` — supervisor delegation (route -> invoke
    specialist -> compose), replicating ``SupervisorAgent.invoke`` semantics.

Security invariants hold on both paths: input/output guardrails, tool execution
through the single authorization boundary (tools/authz.py), bounded tool rounds,
memory append, and audited agent-run persistence.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agents.base import Agent, AgentInput, MAX_TOOL_ROUNDS
from app.gateway.models import ChatMessage, LLMRequest
from app.tools.authz import execute_tool
from app.tools.base import ToolContext

from app.agents.graph.state import AgentGraphState


def _msg(messages: list[dict[str, Any]]) -> list[ChatMessage]:
    return [ChatMessage(**m) for m in messages]


class _ToolNodes:
    """Nodes for the generic specialist tool loop."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    async def call_llm(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        self.agent._guard_input(inp)  # noqa: SLF001

        request = LLMRequest(
            model="",
            provider="",
            messages=_msg(state["messages"]),
            tools=[t.spec() for t in self.agent._available_tools()],  # noqa: SLF001
            json_mode=self.agent._json_output,  # noqa: SLF001
            tenant_id=inp.tenant_id,
        )
        from app.gateway.routing import route_for

        route = route_for(request)
        request.provider = route.provider
        request.model = route.model
        response = await self.agent._call_llm(request)  # noqa: SLF001
        self.agent._guard_output(response.text)  # noqa: SLF001
        self.agent._record_tokens(response.usage)  # noqa: SLF001

        next_state: AgentGraphState = {
            "reply": response.text,
            "token_usage": response.usage,
            "steps": state.get("steps", 0),
        }
        if response.tool_calls:
            next_state["pending_tool_calls"] = [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in response.tool_calls
            ]
        return next_state

    async def execute_tools(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        used: list[str] = []
        outputs: list[dict[str, Any]] = []
        tool_msgs: list[dict[str, Any]] = []

        for tc in state.get("pending_tool_calls", []):
            ctx = ToolContext(
                tenant_id=inp.tenant_id,
                user_id=inp.user_id,
                roles=inp.roles,
                correlation_id=inp.correlation_id,
                resource_owner_id=inp.resource_owner_id,
            )
            try:
                tool_result = await execute_tool(tc["name"], ctx, tc["arguments"])
            except Exception as exc:  # noqa: BLE001 - surfaced to the model as a tool error
                tool_result = type(exc).__name__ + ": " + str(exc)
            used.append(tc["name"])
            outputs.append({"tool": tc["name"], "ok": True, "data": tool_result.data})
            tool_msgs.append(ChatMessage(role="tool", content=str(tool_result.data)).model_dump())

        return {
            "used_tools": used,
            "tool_outputs": outputs,
            "messages": tool_msgs,
            "steps": state.get("steps", 0) + 1,
        }

    async def finalize(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        reply = state.get("reply", "")
        await self.agent._memory.append(  # noqa: SLF001
            inp, reply, state.get("used_tools", [])
        )
        from datetime import UTC, datetime

        start = state.get("started_at", datetime.now(UTC))
        elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
        await self.agent._persist_run(  # noqa: SLF001
            inp,
            state.get("used_tools", []),
            state.get("tool_outputs", []),
            reply,
            start,
        )
        return {
            "needs_human_approval": self.agent.needs_hitl,
            "duration_ms": elapsed,
        }


def _should_execute_tools(state: AgentGraphState) -> str:
    if state.get("pending_tool_calls") and state.get("steps", 0) < MAX_TOOL_ROUNDS:
        return "execute_tools"
    return "finalize"


def _should_loop_tools(state: AgentGraphState) -> str:
    return "call_llm"


def build_tool_graph(agent: Agent):
    """Compile the specialist tool-loop graph (checkpointed per run)."""
    nodes = _ToolNodes(agent)
    builder = StateGraph(AgentGraphState)

    builder.add_node("call_llm", nodes.call_llm)
    builder.add_node("execute_tools", nodes.execute_tools)
    builder.add_node("finalize", nodes.finalize)

    builder.add_edge(START, "call_llm")
    builder.add_conditional_edges("call_llm", _should_execute_tools)
    builder.add_conditional_edges("execute_tools", _should_loop_tools)
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=MemorySaver())


class _SupervisorNodes:
    """Nodes for the supervisor delegation graph."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    async def route(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        self.agent._guard_input(inp)  # noqa: SLF001

        from app.agents.registry import find_by_capability
        from app.agents.router import classify_intent

        intent = classify_intent(inp.message)
        candidates = find_by_capability(intent) if intent else []
        specialist_key = candidates[0].key if candidates else "customer_support"
        return {"specialist_key": specialist_key}

    async def invoke_specialist(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        from app.agents.factory import resolve_agent

        specialist = resolve_agent(state["specialist_key"])
        if specialist is None:
            raise RuntimeError(f"specialist {state['specialist_key']} not registered")

        result = await specialist.invoke(inp)
        return {
            "delegated_to": [specialist.key],
            "specialist_reply": result.reply,
            "specialist_tools": result.used_tools,
            "specialist_outputs": result.tool_outputs,
            "decision": result.decision,
            "needs_human_approval": result.needs_human_approval,
        }

    async def compose(self, state: AgentGraphState, _config: Any = None) -> AgentGraphState:
        inp: AgentInput = state["_input"]
        request = LLMRequest(
            model="",
            provider="",
            messages=[
                ChatMessage(role="system", content=self.agent.system_prompt),
                ChatMessage(
                    role="user",
                    content=f"Customer asked: {inp.message}\n\n"
                    f"Specialist '{state.get('specialist_key')}' returned:\n"
                    f"{state.get('specialist_reply', '')}\n\n"
                    f"Tool outputs: {state.get('specialist_outputs', [])}",
                ),
            ],
            temperature=0.2,
        )
        from app.gateway.routing import route_for

        route = route_for(request)
        request.provider = route.provider
        request.model = route.model
        response = await self.agent._call_llm(request)  # noqa: SLF001
        self.agent._guard_output(response.text)  # noqa: SLF001
        self.agent._record_tokens(response.usage)  # noqa: SLF001

        from datetime import UTC, datetime

        start = state.get("started_at", datetime.now(UTC))
        elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
        await self.agent._persist_run(  # noqa: SLF001
            inp,
            state.get("specialist_tools", []),
            state.get("specialist_outputs", []),
            response.text,
            start,
        )
        await self.agent._memory.append(  # noqa: SLF001
            inp, response.text, state.get("specialist_tools", [])
        )
        return {
            "reply": response.text,
            "token_usage": response.usage,
            "duration_ms": elapsed,
            "needs_human_approval": state.get("needs_human_approval", False),
        }


def build_supervisor_graph(agent: Agent):
    """Compile the supervisor delegation graph (route -> specialist -> compose)."""
    nodes = _SupervisorNodes(agent)
    builder = StateGraph(AgentGraphState)

    builder.add_node("route", nodes.route)
    builder.add_node("invoke_specialist", nodes.invoke_specialist)
    builder.add_node("compose", nodes.compose)

    builder.add_edge(START, "route")
    builder.add_edge("route", "invoke_specialist")
    builder.add_edge("invoke_specialist", "compose")
    builder.add_edge("compose", END)

    return builder.compile(checkpointer=MemorySaver())


def build_agent_graph(agent: Agent):
    """Build the appropriate graph for an agent (supervisor vs specialist)."""
    if agent.key == "supervisor":
        return build_supervisor_graph(agent)
    return build_tool_graph(agent)