"""Developer / Operations Agent — assists platform engineers with runbooks,
incident response, and deployment guidance. Read-only; never mutates infra."""

from __future__ import annotations

from app.agents.base import Agent
from app.tools.document import SearchDocumentsTool


class DevOpsAgent(Agent):
    key = "devops"
    name = "Developer / Operations Agent"
    description = "Assists engineers with runbooks, incidents, and deployment guidance."
    capabilities = ["operations", "devops"]
    routing_priority = 66
    system_prompt = (
        "You assist platform engineers using the operations runbook knowledge base. "
        "Provide step-by-step guidance for incidents and deployments. You never "
        "execute commands or change infrastructure. Escalate incidents per the runbook."
    )

    def _available_tools(self) -> list:
        return [SearchDocumentsTool()]