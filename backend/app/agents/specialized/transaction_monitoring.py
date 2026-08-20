"""Transaction Monitoring Agent — explains transaction risk and helps analysts
investigate flagged transactions. Freezes/blocks are always human-approved."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class TransactionMonitoringAgent(Agent):
    key = "transaction_monitoring"
    name = "Transaction Monitoring Agent"
    description = "Investigates and narrates flagged transactions and AML patterns."
    capabilities = ["aml", "transaction", "monitoring"]
    routing_priority = 45
    needs_hitl = True
    system_prompt = (
        "You help analysts investigate flagged transactions. Explain why a "
        "transaction was flagged (velocity, amount, geography) and gather context. "
        "You never freeze accounts or reverse transactions — that requires the "
        "fraud/AML engine and human approval."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]