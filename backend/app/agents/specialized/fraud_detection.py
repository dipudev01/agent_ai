"""Fraud Detection Agent — assists fraud analysts. The fraud verdict comes from
the deterministic fraud engine in decisioning/fraud.py; the LLM only narrates."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.customer import GetCustomerProfileTool


class FraudDetectionAgent(Agent):
    key = "fraud_detection"
    name = "Fraud Detection Agent"
    description = "Assists fraud analysts with case triage using deterministic fraud scoring."
    capabilities = ["fraud"]
    routing_priority = 25
    needs_hitl = True
    system_prompt = (
        "You assist fraud analysts. You explain fraud-risk scores produced by the "
        "fraud engine and suggest next steps per policy. You never decide to block or "
        "reverse a transaction yourself — those actions require the fraud engine "
        "verdict and human approval."
    )

    def _available_tools(self) -> list:
        return [GetCustomerProfileTool()]