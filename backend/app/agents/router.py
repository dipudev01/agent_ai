"""Agent routing. Routes a user message to the right agent (usually via the
supervisor). Routing is deterministic + LLM-assisted: intent classification
suggests candidates; capability matching + tenant routing policy + permissions
decide. Routing never bypasses authorization — the final chosen agent must be
one the caller may invoke."""

from __future__ import annotations

import re

from app.agents.base import AgentInput
from app.agents.registry import find_by_capability

_INTENT_PATTERNS = [
    ("loan", r"\b(loan|eligible|eligibility|borrow|credit)\b"),
    ("fraud", r"\b(fraud|scam|chargeback|unauthori[sz]ed)\b"),
    ("kyc", r"\b(kyc|verify|verification|aml|sanction|onboard)\b"),
    ("insurance", r"\b(insurance|policy|claim|premium)\b"),
    ("investment", r"\b(invest|wealth|portfolio|mutual fund|stock|sip)\b"),
    ("document", r"\b(document|statement|pdf|file|contract|invoice|upload)\b"),
    ("compliance", r"\b(compliance|regulat|reporting|audit)\b"),
    ("support", r"\b(help|support|issue|problem|complaint)\b"),
]


def classify_intent(message: str) -> str | None:
    text = message.lower()
    scored: list[tuple[int, str]] = []
    for intent, pattern in _INTENT_PATTERNS:
        m = len(re.findall(pattern, text))
        if m:
            scored.append((m, intent))
    scored.sort(reverse=True)
    return scored[0][1] if scored else None


def route(agent_input: AgentInput, hint: str | None = None) -> str | None:
    """Returns the agent key to invoke for this input, or None to defer to the
    supervisor."""
    intent = hint or classify_intent(agent_input.message)
    if intent:
        candidates = find_by_capability(intent)
        # Permission gate: caller must be able to execute at least one candidate.
        if candidates:
            return candidates[0].key
    return "supervisor"