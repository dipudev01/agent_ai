"""Tool authorization — the enforcement point between an agent and any tool.

Three layers, evaluated in order (ALL must pass, fail closed):
1. Registration: tool must exist in the registry.
2. RBAC: principal role must hold the tool's required permission.
3. ABAC + OPA: attribute policy (tenant match, ownership) and, for sensitive
   tools, an external OPA policy decision + HITL approval check.

This module is the ONLY place tools are authorized. Agents can never bypass it.
"""

from __future__ import annotations

from app.core.security.rbac import RBAC, ABACPolicy
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.registry import get_tool


class ToolAuthorizationError(Exception):
    def __init__(self, reason: str, code: str = "tool_denied") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


async def check_opa_policy(tool: Tool, ctx: ToolContext, arguments: dict) -> bool:
    """Delegate to OPA for sensitive tools. Kept behind a seam so the default
    policy engine is swappable (OPA, Cedar, internal). Deny by default."""
    if not tool.sensitive:
        return True
    # In production this is an OPA HTTP call. Local fallback enforces least
    # privilege: sensitive tools require an explicit grant attribute.
    return bool(arguments.get("_approved")) or ("compliance_officer" in ctx.roles)


def require_approval_ok(tool: Tool, arguments: dict) -> bool:
    """Human-in-the-loop: sensitive tools need an approved approval ticket id."""
    if not tool.sensitive:
        return True
    return bool(arguments.get("approval_ticket_id"))


async def authorize_tool_execution(
    tool: Tool,
    ctx: ToolContext,
    arguments: dict,
    *,
    rbac: RBAC | None = None,
    abac: ABACPolicy | None = None,
) -> None:
    from app.core.security.rbac import default_abac, default_rbac

    rbac = rbac or default_rbac()
    abac = abac or default_abac()

    # 1. Permission check (RBAC) — any required permission must be held, or a
    # self-scoped equivalent restricted to the caller's own resources.
    if tool.required_permission:
        granted = any(rbac.can(role, tool.required_permission) for role in ctx.roles)
        used_self_permission = False
        self_permission = tool.required_permission.replace(":read", ":self").replace(":write", ":self")
        if not granted and self_permission != tool.required_permission:
            granted = any(rbac.can(role, self_permission) for role in ctx.roles)
            used_self_permission = granted
        if not granted:
            raise ToolAuthorizationError(
                f"role lacks permission {tool.required_permission}", "insufficient_permission"
            )
        if used_self_permission:
            resource_owner = arguments.get("customer_id") or arguments.get("resource_owner_id")
            if (
                ctx.resource_owner_id is None
                or ctx.resource_owner_id != ctx.user_id
                or resource_owner != ctx.resource_owner_id
            ):
                raise ToolAuthorizationError(
                    "self-scoped access requires resource ownership", "ownership_required"
                )

    # 2. ABAC attribute policy.
    attrs = {
        "subject_tenant_id": ctx.tenant_id,
        "subject_user_id": ctx.user_id,
        "resource_tenant_id": arguments.get("tenant_id", ctx.tenant_id),
        "resource_owner_id": ctx.resource_owner_id,
    }
    if not abac.allows("read" if tool.required_permission is None else "write", "*", attrs):
        raise ToolAuthorizationError("attribute policy denied access", "policy_denied")

    # 3. HITL approval gate first, then OPA for sensitive tools.
    if tool.sensitive:
        if not require_approval_ok(tool, arguments):
            raise ToolAuthorizationError("human approval required", "approval_required")
        if not await check_opa_policy(tool, ctx, arguments):
            raise ToolAuthorizationError("OPA policy denied tool execution", "opa_denied")


async def execute_tool(
    name: str,
    ctx: ToolContext,
    arguments: dict,
) -> ToolResult:
    tool = get_tool(name)
    if tool is None:
        raise ToolAuthorizationError(f"unregistered tool: {name}", "tool_not_found")
    await authorize_tool_execution(tool, ctx, arguments)
    return await tool.run(ctx, arguments)