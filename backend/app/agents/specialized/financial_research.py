"""Financial Research Agent — synthesizes market/company research from permitted
sources. All figures must be sourced; no fabricated data."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.document import SearchDocumentsTool


class FinancialResearchAgent(Agent):
    key = "financial_research"
    name = "Financial Research Agent"
    description = "Produces sourced research summaries over permitted documents and feeds."
    capabilities = ["research", "analysis"]
    routing_priority = 62
    system_prompt = (
        "You produce research summaries over permitted sources. Every figure must be "
        "sourced and cited. If a figure cannot be sourced, omit it. Distinguish facts "
        "from inference and label analysis as such."
    )

    def _available_tools(self) -> list:
        return [SearchDocumentsTool()]