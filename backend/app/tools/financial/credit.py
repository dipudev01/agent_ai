"""Credit bureau report tool. Returns masked credit summary; never raw bureau data."""

from __future__ import annotations

from app.tools.base import Tool, ToolContext, ToolResult

_BUREAU: dict[str, dict] = {
    "cust_1001": {"cibil_score": 742, "on_time_payments_pct": 98.4, "active_loans": 1, "inquiries_6m": 1},
    "cust_1002": {"cibil_score": 512, "on_time_payments_pct": 72.1, "active_loans": 2, "inquiries_6m": 6},
}


class CreditReportTool(Tool):
    name = "get_credit_report"
    description = "Retrieve a masked credit bureau summary for a customer."
    parameters = {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}
    required_permission = "loan:read"

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        customer_id = arguments.get("customer_id", "")
        report = _BUREAU.get(customer_id)
        if report is None:
            return ToolResult.failure(f"no bureau report for {customer_id}")
        if ctx.resource_owner_id and ctx.resource_owner_id != customer_id and "customer:read" not in ctx.roles:
            return ToolResult.failure("bureau report outside your authorized scope")
        return ToolResult.success(credit_report=report, source="demo-bureau")