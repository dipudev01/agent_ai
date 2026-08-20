"""Agent registry and discovery. Agents register here at import time; routing
and delegation resolve by key/capability through this registry only. No agent
holds direct references to other agent instances."""

from __future__ import annotations

from app.agents.base import Agent

_registry: dict[str, Agent] = {}


def register_agent(agent: Agent) -> Agent:
    if agent.key in _registry:
        raise ValueError(f"duplicate agent key: {agent.key}")
    _registry[agent.key] = agent
    return agent


def get_agent(key: str) -> Agent | None:
    return _registry.get(key)


def find_by_capability(capability: str) -> list[Agent]:
    return [a for a in _registry.values() if capability in a.capabilities]


def list_agents() -> dict[str, dict]:
    return {key: agent.spec() for key, agent in sorted(_registry.items())}


def _register_all() -> None:
    from app.agents.specialized.banking_assistant import BankingAssistantAgent
    from app.agents.specialized.collections import CollectionsAgent
    from app.agents.specialized.compliance import ComplianceAgent
    from app.agents.specialized.credit_risk import CreditRiskAgent
    from app.agents.specialized.customer_support import CustomerSupportAgent
    from app.agents.specialized.data_analysis import DataAnalysisAgent
    from app.agents.specialized.devops import DevOpsAgent
    from app.agents.specialized.document import FinancialDocumentAgent
    from app.agents.specialized.financial_research import FinancialResearchAgent
    from app.agents.specialized.fraud_detection import FraudDetectionAgent
    from app.agents.specialized.insurance import InsuranceAgent
    from app.agents.specialized.kyc_aml import KycAmlAgent
    from app.agents.specialized.loan_eligibility import LoanEligibilityAgent
    from app.agents.specialized.regulatory_intel import RegulatoryIntelligenceAgent
    from app.agents.specialized.supervisor import SupervisorAgent
    from app.agents.specialized.transaction_monitoring import TransactionMonitoringAgent
    from app.agents.specialized.wealth import WealthAgent

    for agent in (
        SupervisorAgent(),
        CustomerSupportAgent(),
        BankingAssistantAgent(),
        LoanEligibilityAgent(),
        CreditRiskAgent(),
        FraudDetectionAgent(),
        KycAmlAgent(),
        TransactionMonitoringAgent(),
        FinancialDocumentAgent(),
        InsuranceAgent(),
        WealthAgent(),
        CollectionsAgent(),
        ComplianceAgent(),
        RegulatoryIntelligenceAgent(),
        FinancialResearchAgent(),
        DataAnalysisAgent(),
        DevOpsAgent(),
    ):
        register_agent(agent)


_register_all()