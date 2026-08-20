"""Tool registry — the ONLY place tools are registered. Agents can only invoke
tools present here. Unknown or unregistered tool names are rejected at the
gateway before they reach any implementation."""

from __future__ import annotations

from app.gateway.models import ToolSpec
from app.tools.base import Tool

_registry: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    if tool.name in _registry:
        raise ValueError(f"duplicate tool registration: {tool.name}")
    _registry[tool.name] = tool
    return tool


def get_tool(name: str) -> Tool | None:
    return _registry.get(name)


def list_tools() -> dict[str, Tool]:
    return dict(_registry)


def list_specs() -> list[ToolSpec]:
    return [t.spec() for t in _registry.values()]


def _register_all() -> None:
    from app.tools.compliance import SanctionsScreenTool
    from app.tools.customer import GetCustomerProfileTool
    from app.tools.document import SearchDocumentsTool
    from app.tools.financial.credit import CreditReportTool
    from app.tools.financial.eligibility import EligibilityCheckTool
    from app.tools.financial.kyc import KYCCheckTool

    for tool in (
        EligibilityCheckTool(),
        CreditReportTool(),
        KYCCheckTool(),
        GetCustomerProfileTool(),
        SearchDocumentsTool(),
        SanctionsScreenTool(),
    ):
        register(tool)


_register_all()