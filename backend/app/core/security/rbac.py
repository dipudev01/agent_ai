"""RBAC + ABAC authorization primitives.

RBAC: role -> permission mapping (static, per tenant).
ABAC: attribute-based conditions evaluated at decision time (resource, context).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Permission:
    action: str  # e.g. "loan:read", "customer:write", "agent:execute"
    resource: str  # e.g. "loan", "customer", "agent", "document", "audit"
    scope: str = "tenant"  # tenant | institution | platform


class RBAC:
    """Static role -> permission mapping."""

    def __init__(self, role_permissions: dict[str, set[str]] | None = None) -> None:
        self._role_permissions = role_permissions or {}

    def grant(self, role: str, permission: str) -> None:
        self._role_permissions.setdefault(role, set()).add(permission)

    def can(self, role: str, permission: str) -> bool:
        return permission in self._role_permissions.get(role, set())


class ABACPolicy:
    """Attribute-based rule: (action, resource) -> callable(attributes) -> bool."""

    def __init__(self) -> None:
        self._rules: list[tuple[str, str, callable]] = []

    def add(self, action: str, resource: str, condition: callable) -> None:
        self._rules.append((action, resource, condition))

    def allows(self, action: str, resource: str, attributes: dict[str, Any]) -> bool:
        applicable = [c for a, r, c in self._rules if a == action and r == resource]
        if not applicable:
            return False  # deny by default (fail closed)
        return all(c(attributes) for c in applicable)


def default_rbac() -> RBAC:
    rbac = RBAC()
    # Platform roles
    rbac.grant("platform_admin", "tenant:*")
    rbac.grant("platform_admin", "institution:*")
    # Institution roles
    rbac.grant("institution_admin", "institution:*")
    rbac.grant("institution_admin", "loan:read")
    rbac.grant("institution_admin", "customer:read")
    # Staff roles
    rbac.grant("loan_officer", "loan:read")
    rbac.grant("loan_officer", "loan:write")
    rbac.grant("loan_officer", "customer:read")
    rbac.grant("compliance_officer", "compliance:*")
    rbac.grant("compliance_officer", "audit:read")
    rbac.grant("fraud_analyst", "fraud:read")
    rbac.grant("fraud_analyst", "fraud:write")
    # Customer roles
    rbac.grant("customer", "customer:self")
    rbac.grant("customer", "loan:self")
    return rbac


def default_abac() -> ABACPolicy:
    abac = ABACPolicy()
    # Tenant-scoped resource access: subject.tenant_id must equal resource.tenant_id
    abac.add("read", "*", lambda attrs: _same_tenant(attrs))
    abac.add("write", "*", lambda attrs: _same_tenant(attrs))
    # Self-service: customer can only touch their own profile/loans
    abac.add("*", "customer:self", lambda attrs: _is_owner(attrs))
    abac.add("*", "loan:self", lambda attrs: _is_owner(attrs))
    return abac


def _same_tenant(attrs: dict[str, Any]) -> bool:
    return attrs.get("subject_tenant_id") == attrs.get("resource_tenant_id")


def _is_owner(attrs: dict[str, Any]) -> bool:
    return attrs.get("subject_user_id") == attrs.get("resource_owner_id")