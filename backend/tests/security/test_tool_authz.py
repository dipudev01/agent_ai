"""Tool authorization tests — verify the enforcement layers: registry check,
RBAC, ABAC, OPA/HITL for sensitive tools. Fail-closed by default."""

import pytest

from app.core.security.rbac import default_rbac
from app.tools.authz import ToolAuthorizationError, authorize_tool_execution
from app.tools.base import ToolContext
from app.tools.registry import get_tool


def _ctx(tenant="t1", user="u1", roles=("customer",)) -> ToolContext:
    return ToolContext(tenant_id=tenant, user_id=user, roles=list(roles), correlation_id="test")


async def test_customer_can_read_own_profile():
    tool = get_tool("get_customer_profile")
    ctx = _ctx()
    await authorize_tool_execution(tool, ctx, {"customer_id": "u1"}, rbac=default_rbac())
    # no exception = allowed


async def test_customer_denied_bureau_read():
    # get_credit_report requires loan:read; customer lacks it.
    tool = get_tool("get_credit_report")
    ctx = _ctx()
    with pytest.raises(ToolAuthorizationError) as e:
        await authorize_tool_execution(tool, ctx, {"customer_id": "u1"}, rbac=default_rbac())
    assert e.value.code == "insufficient_permission"


async def test_unregistered_tool_denied():
    from app.tools.authz import execute_tool

    with pytest.raises(ToolAuthorizationError) as e:
        await execute_tool("does_not_exist", _ctx(), {})
    assert e.value.code == "tool_not_found"


async def test_sensitive_tool_requires_approval():
    tool = get_tool("check_loan_eligibility")
    ctx = _ctx(roles=("loan_officer",))
    with pytest.raises(ToolAuthorizationError) as e:
        await authorize_tool_execution(tool, ctx, {"customer_id": "c1"}, rbac=default_rbac())
    assert e.value.code == "approval_required"


async def test_sensitive_tool_with_approval_and_role_passes():
    tool = get_tool("check_loan_eligibility")
    ctx = _ctx(roles=("loan_officer",))
    await authorize_tool_execution(
        tool,
        ctx,
        {"customer_id": "c1", "approval_ticket_id": "AP-001", "_approved": True},
        rbac=default_rbac(),
    )


async def test_sanctions_screen_compliance_only():
    tool = get_tool("sanctions_screen")
    with pytest.raises(ToolAuthorizationError):
        await authorize_tool_execution(tool, _ctx(), {"party_name": "x"}, rbac=default_rbac())