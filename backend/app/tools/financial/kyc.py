"""KYC status tool. Never returns raw KYC documents to agents — only status."""

from __future__ import annotations

from app.tools.base import Tool, ToolContext, ToolResult

_STATUS = {
    "cust_1001": {"kyc_status": "verified", "level": "L2", "verified_at": "2026-01-15", "aml_pending": False},
    "cust_1002": {"kyc_status": "pending", "level": "L0", "verified_at": None, "aml_pending": True},
}


class KYCCheckTool(Tool):
    name = "check_kyc_status"
    description = "Check a customer's KYC/AML verification status."
    parameters = {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}
    required_permission = "customer:read"

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        customer_id = arguments.get("customer_id", "")
        status = _STATUS.get(customer_id)
        if status is None:
            return ToolResult.failure(f"no KYC record for {customer_id}")
        return ToolResult.success(**status)