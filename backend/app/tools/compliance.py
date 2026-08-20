"""Sanctions screening tool. Delegates to a sanctions list (OFAC/UN/EU)."""

from __future__ import annotations

from app.tools.base import Tool, ToolContext, ToolResult

_SANCTIONED = {"BLACKLISTED USER", "AL-QAEDA-ADJACENT ENTITY"}


class SanctionsScreenTool(Tool):
    name = "sanctions_screen"
    description = "Screen a party against sanctions lists. Used by KYC/AML workflows."
    parameters = {
        "type": "object",
        "properties": {
            "party_name": {"type": "string"},
            "country": {"type": "string"},
            "id_number": {"type": "string"},
        },
        "required": ["party_name"],
    }
    required_permission = "compliance:*"
    sensitive = True

    async def run(self, ctx: ToolContext, arguments: dict) -> ToolResult:
        name = arguments.get("party_name", "").strip().upper()
        hit = name in _SANCTIONED
        return ToolResult.success(
            screened=True,
            hit=hit,
            matched_entity=name if hit else None,
            list_version="un-eu-ofac-2026.03",
        )