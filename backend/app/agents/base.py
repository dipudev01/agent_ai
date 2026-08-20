"""Agent abstraction and lifecycle.

Lifecycle: registered → discoverable → routed → invoked → executed → evaluated
→ recorded. Every execution is audited as an AgentRun. Agents speak to the world
only through authorized tools (app/tools/authz.py). Agents can delegate to other
agents only through the registry (no direct object references).

Guardrails are enforced on BOTH the inputs (prompt injection) and outputs
(validation, jailbreak, hallucination checks) before an agent's reply leaves the
platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.agents.memory import AgentMemory
from app.core.container import container
from app.gateway.models import ChatMessage, LLMRequest
from app.tools.authz import execute_tool
from app.tools.base import ToolContext, ToolResult

MAX_TOOL_ROUNDS = 6


class GuardrailError(Exception): ...


@dataclass
class AgentInput:
    tenant_id: str
    user_id: str
    roles: list[str]
    correlation_id: str
    message: str
    conversation_id: str | None = None
    context: dict = field(default_factory=dict)
    resource_owner_id: str | None = None


@dataclass
class AgentResult:
    reply: str
    used_tools: list[str] = field(default_factory=list)
    tool_outputs: list[dict] = field(default_factory=list)
    delegated_to: list[str] = field(default_factory=list)
    duration_ms: int = 0
    token_usage: dict = field(default_factory=dict)
    needs_human_approval: bool = False
    decision: dict | None = None

    def to_dict(self) -> dict:
        return {
            "reply": self.reply,
            "used_tools": self.used_tools,
            "delegated_to": self.delegated_to,
            "duration_ms": self.duration_ms,
            "token_usage": self.token_usage,
            "needs_human_approval": self.needs_human_approval,
            "decision": self.decision,
        }


class Agent(ABC):
    key: str  # unique registry key
    name: str
    description: str
    capabilities: list[str] = []
    routing_priority: int = 100
    version: str = "1.0.0"
    needs_hitl: bool = False
    system_prompt: str = ""

    def __init__(self, memory: AgentMemory | None = None) -> None:
        self._memory = memory or AgentMemory()
        self._last_usage: dict = {}

    def spec(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "routing_priority": self.routing_priority,
            "version": self.version,
            "needs_hitl": self.needs_hitl,
        }

    async def invoke(self, inp: AgentInput) -> AgentResult:
        start = datetime.now(UTC)
        self._guard_input(inp)

        # Reconstruct short-term memory (conversation history).
        history = await self._memory.get_short_term(inp.conversation_id, inp.tenant_id, inp.user_id)
        messages = [ChatMessage(role="system", content=self.system_prompt)]
        messages.extend(history)
        messages.append(ChatMessage(role="user", content=inp.message))

        used_tools: list[str] = []
        tool_outputs: list[dict] = []
        reply_text = ""

        for _ in range(MAX_TOOL_ROUNDS):
            request = LLMRequest(
                model=container.llm()._default_model,  # noqa: SLF001 — model default
                provider="mock",
                messages=messages,
                tools=[t.spec() for t in self._available_tools()],
                json_mode=self._json_output,
                tenant_id=inp.tenant_id,
            )
            response = await self._call_llm(request)
            self._guard_output(response.text)

            if response.tool_calls:
                for tc in response.tool_calls:
                    ctx = ToolContext(
                        tenant_id=inp.tenant_id,
                        user_id=inp.user_id,
                        roles=inp.roles,
                        correlation_id=inp.correlation_id,
                        resource_owner_id=inp.resource_owner_id,
                    )
                    try:
                        result = await execute_tool(tc.name, ctx, tc.arguments)
                    except Exception as exc:
                        result = ToolResult.failure(f"{type(exc).__name__}: {exc}")
                    used_tools.append(tc.name)
                    tool_outputs.append({"tool": tc.name, "ok": result.ok, "data": result.data})
                    messages.append(ChatMessage(role="tool", content=repr(result.data)))
                continue

            reply_text = response.text
            self._record_tokens(response.usage)
            break

        await self._memory.append(inp, reply_text, used_tools)
        await self._persist_run(inp, used_tools, tool_outputs, reply_text, start)
        result = AgentResult(
            reply=reply_text,
            used_tools=used_tools,
            tool_outputs=tool_outputs,
            token_usage=self._last_usage,
            needs_human_approval=self.needs_hitl,
        )
        if not reply_text:
            result.reply = "I could not complete that request. Please retry or contact support."
        return result

    # ---- extension points ----
    @abstractmethod
    def _available_tools(self) -> list: ...

    @property
    def _json_output(self) -> bool:
        return False

    def _guard_input(self, inp: AgentInput) -> None:
        from app.core.security.guardrails import detect_prompt_injection

        if detect_prompt_injection(inp.message):
            raise GuardrailError("input rejected by guardrail")

    def _guard_output(self, text: str) -> None:
        from app.core.security.guardrails import detect_jailbreak_attempt, detect_hallucination_marker

        if detect_jailbreak_attempt(text):
            raise GuardrailError("output rejected by guardrail")
        if detect_hallucination_marker(text):
            raise GuardrailError("output failed hallucination validation")

    async def _call_llm(self, request: LLMRequest):
        return await container.llm().complete(request)

    def _record_tokens(self, usage: dict) -> None:
        self._last_usage = usage

    async def _persist_run(self, inp, tools, outputs, reply, start) -> None:
        from app.services.audit import record_agent_run

        elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
        await record_agent_run(
            tenant_id=inp.tenant_id,
            run_id=inp.correlation_id,
            agent_key=self.key,
            conversation_id=inp.conversation_id,
            user_id=inp.user_id,
            status="completed",
            input_schema={"message": inp.message},
            output_schema={"reply": reply, "tools": tools, "outputs": outputs},
            latency_ms=elapsed,
            token_usage=self._last_usage,
            model_version=self.version,
        )