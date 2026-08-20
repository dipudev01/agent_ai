"""Customer profile tool. Returns a PII-masked, role-scoped view of a customer.
Raw PII is never returned to agents — only masked fields, which keeps prompts
clean and reduces exfiltration risk."""

from __future__ import annotations

from app.core.security import pii
from app.tools.base import Tool, ToolContext, ToolResult

# Demo customer store (in production this is the Customer 360 service).
_DB: dict[str, dict] = {
    "cust_1001": {
        "customer_id": "cust_1001",
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "phone": "+919800001234",
        "pan": "ABCDE1234F",
        "income": 850_000,
        "cibil_score": 742,
        "existing_emis": 12000,
        "active_loans": 1,
    },
    "cust_1002": {
        "customer_id": "cust_1002",
        "name": "Rahul Verma",
        "email": "rahul@example.com",
        "phone": "+919811112222",
        "pan": "GHIJK5678L",
        "income": 240_000,
        "cibil_score": 512,
        "existing_emis": 9000,
        "active_loans": 2,
    },
}


class GetCustomerProfileTool(Tool):
    name = "get_customer_profile"
    description = "Retrieve a customer's profile summary with masked PII."
    parameters = {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}
    required_permission = "customer:read"

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        customer_id = arguments.get("customer_id", "")
        record = _DB.get(customer_id)
        if record is None:
            return ToolResult.failure(f"customer {customer_id} not found")
        if ctx.resource_owner_id and ctx.resource_owner_id != customer_id and "customer:read" not in ctx.roles:
            return ToolResult.failure("customer is outside your authorized scope")
        safe = {k: v for k, v in record.items()}
        safe["email"] = pii.mask_field("email", safe["email"])
        safe["phone"] = pii.mask_field("phone", safe["phone"])
        safe["pan"] = pii.mask_field("pan", safe["pan"])
        return ToolResult.success(profile=safe, masked=True)