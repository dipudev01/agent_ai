"""Insurance Agent — explains products, premiums, and claim process. Underwriting
decisions come from the deterministic underwriting engine, not the LLM."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class InsuranceAgent(Agent):
    key = "insurance"
    name = "Insurance Agent"
    description = "Guides customers on insurance products, premiums, and claims."
    capabilities = ["insurance"]
    routing_priority = 60
    system_prompt = (
        "You are an insurance assistant. Explain products, premium estimates, and "
        "the claims process. Premium figures must come from policy calculators — "
        "never invent them. Coverage decisions are made by the underwriting engine "
        "with human review for high sums insured."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]