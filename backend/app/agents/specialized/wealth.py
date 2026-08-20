"""Investment / Wealth Agent — general investment education and portfolio
guidance. It NEVER gives personalized investment advice without a licensed
advisor and model governance approval. Disclaimers are mandatory."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class WealthAgent(Agent):
    key = "wealth"
    name = "Investment / Wealth Agent"
    description = "Educational investment guidance and portfolio support."
    capabilities = ["investment", "wealth", "portfolio"]
    routing_priority = 65
    system_prompt = (
        "You provide educational information about investing: product types, risk "
        "concepts, and market basics. You do not give personalized investment advice "
        "or recommendations. Any recommendation requires a licensed advisor and model "
        "governance approval. Always include a disclaimer that investing involves risk "
        "and past performance does not guarantee future returns."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]