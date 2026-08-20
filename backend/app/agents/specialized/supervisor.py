"""Supervisor / orchestrator agent. Routes user requests to the right specialist,
coordinate delegation, and composes a final answer. It never executes financial
decision tools itself — it delegates to specialists whose decisions are
deterministic and audited."""

from __future__ import annotations

from app.agents.base import Agent, AgentInput, AgentResult
from app.agents.registry import find_by_capability
from app.agents.router import classify_intent
from app.core.container import container
from app.gateway.models import ChatMessage, LLMRequest

SYSTEM_PROMPT = (
    "You are the Supervisor of a financial services agent platform for a bank or fintech. "
    "You coordinate specialist agents. You never invent financial figures or decisions. "
    "You route requests to the specialist with the right capability and synthesize their "
    "output for the customer. If a request involves eligibility, fraud, credit, or KYC, you "
    "MUST delegate to the specialist and relay only their deterministic output. You never "
    "give a loan decision, credit decision, or fraud verdict yourself."
)


class SupervisorAgent(Agent):
    key = "supervisor"
    name = "Supervisor / Orchestrator Agent"
    description = "Coordinates specialist agents and composes responses for the user."
    capabilities = ["orchestrate"]
    routing_priority = 0
    system_prompt = SYSTEM_PROMPT

    def _available_tools(self) -> list:
        return []

    async def invoke(self, inp: AgentInput) -> AgentResult:
        intent = classify_intent(inp.message)
        candidates = find_by_capability(intent) if intent else []
        delegated: list[str] = []

        # Delegate to the most specific specialist; we trust the registry, not the
        # model, to choose who to call.
        specialist = candidates[0] if candidates else None
        if specialist is None:
            from app.agents.registry import get_agent

            specialist = get_agent("customer_support")
        if specialist is None:
            raise RuntimeError("customer_support agent not registered")

        result = await specialist.invoke(inp)
        delegated.append(specialist.key)

        # Compose final answer from the specialist's deterministic output.
        request = LLMRequest(
            model="mock",
            provider="mock",
            messages=[
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=f"Customer asked: {inp.message}\n\n"
                    f"Specialist '{specialist.key}' returned:\n{result.reply}\n\n"
                    f"Tool outputs: {result.tool_outputs}",
                ),
            ],
            temperature=0.2,
        )
        response = await container.llm().complete(request)
        self._guard_output(response.text)

        result.reply = response.text
        result.delegated_to = delegated
        result.decision = result.decision  # preserved from specialist
        return result