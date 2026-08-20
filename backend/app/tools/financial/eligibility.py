"""Deterministic eligibility check tool. The actual decision comes from the
decisioning engine; the agent only narrates it. Marked sensitive: any
eligibility output that could be presented as a pre-approved offer requires HITL
sign-off before it is shown to the customer."""

from __future__ import annotations

from app.decisioning.eligibility import assess_eligibility
from app.tools.base import Tool, ToolContext, ToolResult


class EligibilityCheckTool(Tool):
    name = "check_loan_eligibility"
    description = "Deterministic loan eligibility assessment. Returns explainable decision with reasons."
    parameters = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "income": {"type": "number"},
            "cibil_score": {"type": "integer"},
            "existing_emis": {"type": "number"},
            "requested_amount": {"type": "number"},
            "tenure_months": {"type": "integer"},
        },
        "required": ["customer_id", "income", "cibil_score", "existing_emis", "requested_amount", "tenure_months"],
    }
    required_permission = "loan:read"
    sensitive = True

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        decision = assess_eligibility(
            income=arguments["income"],
            cibil_score=arguments["cibil_score"],
            existing_emis=arguments["existing_emis"],
            requested_amount=arguments["requested_amount"],
            tenure_months=arguments["tenure_months"],
        )
        return ToolResult.success(
            decision=decision.to_dict(),
            advisory_note="Decision is deterministic and policy-controlled; not an LLM output.",
        )