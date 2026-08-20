"""Financial Document Agent — extracts and summarizes financial documents
(statements, contracts, policies) through the RAG pipeline. Access is always
ACL-checked by the document tool."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.document import SearchDocumentsTool


class FinancialDocumentAgent(Agent):
    key = "financial_document"
    name = "Financial Document Agent"
    description = "Extracts, summarizes, and answers questions over financial documents."
    capabilities = ["document", "extraction", "rag"]
    routing_priority = 50
    system_prompt = (
        "You answer questions over financial documents using retrieval only. Cite "
        "the document and section you used. If retrieval returns nothing relevant, "
        "say so. Never invent figures, clauses, or policy details. Respect document "
        "permissions — you can only see documents you are allowed to read."
    )

    def _available_tools(self) -> list:
        return [SearchDocumentsTool()]