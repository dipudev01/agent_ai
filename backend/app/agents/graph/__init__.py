"""LangGraph-based agent orchestration (optional).

Selected via ``settings.agent_orchestrator``. Kept behind lazy imports so the
classic loop remains the default and importing the app never requires langgraph.
"""

from __future__ import annotations

from app.agents.graph.agent import LangGraphAgent

__all__ = ["LangGraphAgent"]