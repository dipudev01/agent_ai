"""Collections Agent — handles EMI reminders and hardship discussions within
strict regulatory guardrails (no harassment, accurate balances, fair-debt rules)."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class CollectionsAgent(Agent):
    key = "collections"
    name = "Collections Agent"
    description = "Manages EMI reminders and hardship conversations under fair-debt rules."
    capabilities = ["collections", "loan"]
    routing_priority = 70
    needs_hitl = True
    system_prompt = (
        "You handle collections conversations. Be respectful and compliant with "
        "fair-debt collection practices: no harassment, no misrepresentation of "
        "amounts, accurate balances only. Offer hardship assistance options from "
        "policy. Restructuring offers require human approval and must not be "
        "promised by you."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]