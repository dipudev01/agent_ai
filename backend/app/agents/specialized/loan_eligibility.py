"""Loan Eligibility Agent — routes to the deterministic eligibility engine.
The LLM only narrates the deterministic decision; it never computes eligibility."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool
from app.tools.financial.credit import CreditReportTool
from app.tools.financial.eligibility import EligibilityCheckTool


class LoanEligibilityAgent(Agent):
    key = "loan_eligibility"
    name = "Loan Eligibility Agent"
    description = "Deterministic loan eligibility assessment with explainable reasons."
    capabilities = ["loan", "eligibility", "credit"]
    routing_priority = 30
    needs_hitl = True  # presenting a pre-approved amount requires human sign-off
    system_prompt = (
        "You assess loan eligibility using the deterministic eligibility engine only. "
        "You gather customer profile and credit report via tools, then call the "
        "eligibility tool. You report the decision and its reasons verbatim. You never "
        "compute scores or amounts yourself, and you never commit to an offer without "
        "the decision object. Flag that any pre-approved amount requires final human "
        "approval before it can be considered an offer."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool(), CreditReportTool(), EligibilityCheckTool()]

    @property
    def _json_output(self) -> bool:
        return True