"""Customer Support Agent — handles general queries, complaints, guidance.
No sensitive financial decisions; may read masked customer profile."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class CustomerSupportAgent(Agent):
    key = "customer_support"
    name = "Customer Support Agent"
    description = "Handles general support queries, complaints, and guidance."
    capabilities = ["support", "general"]
    routing_priority = 90
    system_prompt = (
        "You are a customer support agent for a financial institution. Be empathetic, "
        "clear, and concise. You may look up a customer's masked profile when the "
        "customer identity is confirmed. Never share raw PII. Never state balances or "
        "limits you have not verified. Escalate complaints to the human team."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]