"""Credit Risk Agent — surfaces credit risk analytics to risk teams. Decisions
about credit exposure are always made by the deterministic credit-risk model in
decisioning/, never by the LLM."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.financial.credit import CreditReportTool
from app.tools.customer import GetCustomerProfileTool


class CreditRiskAgent(Agent):
    key = "credit_risk"
    name = "Credit Risk Agent"
    description = "Surfaces credit risk analytics and portfolio risk insights for risk teams."
    capabilities = ["credit", "risk"]
    routing_priority = 40
    system_prompt = (
        "You assist risk teams with credit analytics. Pull masked credit reports and "
        "customer profiles. Summarize risk signals. You do not set policy, and you "
        "never approve or decline credit — that is the credit-risk model's job."
    )

    def _available_tools(self) -> list:
        return [CreditReportTool(), GetCustomerProfileTool()]