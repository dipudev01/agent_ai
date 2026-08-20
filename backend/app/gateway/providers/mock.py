"""Scripted default LLM provider for local dev, tests, and demos.

Deterministic and side-effect free. When tools are advertised and the user
message matches a tool's intent keywords, it emits a tool call with canned
arguments. When the last message is a tool result, it produces a summary reply.
This makes agent behavior tests meaningful without network access.
"""

from __future__ import annotations

from app.gateway.llm import LLMProvider
from app.gateway.models import LLMRequest, LLMResponse, ToolCall

_TOOL_INTENTS: dict[str, tuple[list[str], dict]] = {
    "get_customer_profile": (
        ["profile", "customer", "account details", "my details", "kyc status"],
        {"customer_id": "cust_1001"},
    ),
    "get_credit_report": (
        ["credit", "cibil", "bureau", "credit score"],
        {"customer_id": "cust_1001"},
    ),
    "check_loan_eligibility": (
        ["loan", "eligibility", "borrow", "lakh", "emi"],
        {
            "customer_id": "cust_1001",
            "income": 850000,
            "cibil_score": 742,
            "existing_emis": 12000,
            "requested_amount": 1000000,
            "tenure_months": 60,
            "approval_ticket_id": "AP-001",
            "_approved": True,
        },
    ),
    "check_kyc_status": (
        ["kyc", "verification", "onboard"],
        {"customer_id": "cust_1001"},
    ),
    "sanctions_screen": (
        ["sanction", "aml", "screen"],
        {"party_name": "Priya Sharma"},
    ),
    "search_documents": (
        ["document", "statement", "pdf", "policy", "contract", "invoice"],
        {"query": "terms", "top_k": 3},
    ),
}


class MockLLMProvider(LLMProvider):
    name = "mock"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last = request.messages[-1] if request.messages else None

        # Tool result present → summarize it into a final reply.
        if last is not None and last.role == "tool":
            return LLMResponse(
                text=f"Based on the tool output: {last.content[:400]}",
                model=request.model,
                provider=self.name,
                usage={"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
                finish_reason="stop",
            )

        # Otherwise, if a tool intent matches, emit a scripted tool call.
        if request.tools and last is not None:
            text = last.content.lower()
            for tool in request.tools:
                keywords, args = _TOOL_INTENTS.get(tool.name, ((), {}))
                if any(k in text for k in keywords):
                    return LLMResponse(
                        text="",
                        tool_calls=[ToolCall(id=f"call_{tool.name}", name=tool.name, arguments=args)],
                        model=request.model,
                        provider=self.name,
                        usage={"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
                        finish_reason="tool_calls",
                    )

        # Default: echo (still deterministic, no tool calls).
        content = last.content if last else ""
        text = (
            f"[mock:{request.model}] echo: {content[:200]}"
            + ("\nRequested JSON output." if request.json_mode else "")
        )
        return LLMResponse(
            text=text,
            model=request.model,
            provider=self.name,
            usage={"prompt_tokens": 10, "completion_tokens": len(text.split()), "total_tokens": 10},
        )