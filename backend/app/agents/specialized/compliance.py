"""Compliance Agent — answers compliance questions, surfaces obligations, and
prepares evidence packs for regulators. Facts must come from the policy/RAG
knowledge base, never invented."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.compliance import SanctionsScreenTool
from app.tools.document import SearchDocumentsTool


class ComplianceAgent(Agent):
    key = "compliance"
    name = "Compliance Agent"
    description = "Answers compliance questions and prepares regulatory evidence packs."
    capabilities = ["compliance", "regulatory"]
    routing_priority = 55
    system_prompt = (
        "You support the compliance team. Answer questions using the policy "
        "knowledge base only and cite your sources. Prepare evidence packs from "
        "audit and document data. You do not interpret law — flag questions that "
        "require legal counsel for the compliance officer."
    )

    def _available_tools(self) -> list:
        return [SearchDocumentsTool(), SanctionsScreenTool()]