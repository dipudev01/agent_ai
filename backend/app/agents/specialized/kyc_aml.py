"""KYC/AML Agent — walks customers through KYC, runs sanctions screening, and
flags AML signals. Onboarding decisions require compliance approval (HITL)."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.compliance import SanctionsScreenTool
from app.tools.financial.kyc import KYCCheckTool


class KycAmlAgent(Agent):
    key = "kyc_aml"
    name = "KYC/AML Agent"
    description = "Guides KYC onboarding and runs sanctions and AML checks."
    capabilities = ["kyc", "aml", "onboarding"]
    routing_priority = 35
    needs_hitl = True
    system_prompt = (
        "You support KYC/AML workflows. Run sanctions screening for onboarding. "
        "Explain document requirements. Flag AML signals to the compliance team. "
        "Never declare a customer fully onboarded — final approval requires "
        "compliance officer sign-off."
    )

    def _available_tools(self) -> list:
        return [SanctionsScreenTool(), KYCCheckTool()]