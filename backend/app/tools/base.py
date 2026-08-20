"""Tool abstraction. A Tool is the ONLY way an agent can touch the outside
world. Every tool is registered in app/tools/registry.py and authorized by
app/tools/authz.py. Tools run inside the tenant context of the requesting user.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.gateway.models import ToolSpec


@dataclass
class ToolContext:
    tenant_id: str
    user_id: str
    roles: list[str]
    correlation_id: str
    resource_owner_id: str | None = None


@dataclass
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def success(cls, **data) -> "ToolResult":
        return cls(ok=True, data=data)

    @classmethod
    def failure(cls, error: str) -> "ToolResult":
        return cls(ok=False, error=error)


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any] = {}
    # Permission required to execute; None means no tool-specific permission.
    required_permission: str | None = None
    # True if execution must go through OPA + HITL (high-impact financial action).
    sensitive: bool = False

    @abstractmethod
    async def run(self, ctx: ToolContext, arguments: dict[str, Any]) -> ToolResult: ...

    def spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description, parameters=self.parameters)