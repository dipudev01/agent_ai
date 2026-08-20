"""Data Analysis Agent — SQL/analytics assistance for data teams. Reads only
from read replicas / warehouse through a read-only, gated query tool. Never
mutates production data."""

from __future__ import annotations

from app.agents.base import Agent


class DataAnalysisAgent(Agent):
    key = "data_analysis"
    name = "Data Analysis Agent"
    description = "Assists data teams with SQL and analytics over read-only data."
    capabilities = ["analysis", "data"]
    routing_priority = 64
    system_prompt = (
        "You assist data teams with analytics. Generate read-only SQL for the "
        "warehouse. Never produce queries that mutate data. Mask any PII in results "
        "and summarize insights."
    )

    def _available_tools(self) -> list:
        return []  # gated read-only query tool wired in production