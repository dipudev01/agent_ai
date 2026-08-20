"""Regulatory Intelligence Agent — monitors regulatory changes (RBI circulars,
DPDP, AML) and summarizes impact. Requires an external regulatory feed in
production; never fabricates regulation."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.document import SearchDocumentsTool


class RegulatoryIntelligenceAgent(Agent):
    key = "regulatory_intelligence"
    name = "Regulatory Intelligence Agent"
    description = "Monitors and summarizes regulatory changes and their business impact."
    capabilities = ["regulatory", "compliance"]
    routing_priority = 58
    system_prompt = (
        "You track regulatory developments from the curated regulatory feed. "
        "Summarize changes and their impact on operations. Cite the source circular "
        "or gazette. Never invent regulations or dates. Flag items needing the "
        "compliance officer's legal review."
    )

    def _available_tools(self) -> list:
        return [SearchDocumentsTool()]