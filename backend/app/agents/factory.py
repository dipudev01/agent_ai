"""Agent instance resolution. Chooses the orchestration strategy based on
settings (classic loop vs LangGraph StateGraph) while keeping the registry and
the Agent contract identical for callers.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.agents.registry import get_agent
from app.core.config import settings


def _wrap_langgraph(agent: Agent) -> Agent:
    """Lazily import the LangGraph wrapper (keeps classic path dependency-free)."""
    from app.agents.graph import LangGraphAgent

    return LangGraphAgent(agent)


def resolve_agent(key: str, orchestrator: str | None = None) -> Agent | None:
    """Resolve an agent by registry key, applying the configured orchestrator.

    The orchestrator defaults to settings at call time; tests may override by
    passing an explicit value or patching settings.agent_orchestrator.
    """
    agent = get_agent(key)
    if agent is None:
        return None
    orch = orchestrator or settings.agent_orchestrator
    if orch == "langgraph":
        return _wrap_langgraph(agent)
    return agent