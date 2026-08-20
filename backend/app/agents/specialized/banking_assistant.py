"""Banking Assistant Agent — everyday banking guidance, product discovery,
digital banking navigation. Delegates eligibility to the Loan Eligibility Agent."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class BankingAssistantAgent(Agent):
    key = "banking_assistant"
    name = "Banking Assistant Agent"
    description = "Guides customers through banking products and digital banking services."
    capabilities = ["banking", "product", "general"]
    routing_priority = 80
    system_prompt = (
        "You are a banking assistant. Help customers understand products (savings, "
        "current accounts, FD/RD, cards), digital banking features, and fees. Use the "
        "masked customer profile for personalization. For loan eligibility, direct the "
        "customer to the loan eligibility flow. Never reveal another customer's data."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]