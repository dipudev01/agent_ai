"""AI guardrails: prompt-injection detection, jailbreak detection, and output
validation. These are heuristic, first-line checks. Production adds model-based
judges and policy reviews. Fail closed — any detected violation rejects the
input or output."""

from __future__ import annotations

import re

# Prompt-injection indicators in user input.
_INJECTION_PATTERNS = re.compile(
    r"ignore (all )?(previous|prior|above|earlier) (instructions|prompts|rules)"
    r"|disregard (your )?instructions"
    r"|you are now |act as (an? )?(developer|system|admin)"
    r"|forget everything|forget your (role|prompt|instructions)"
    r"|jailbreak|dan mode|do anything now"
    r"|reveal your (system )?prompt|print your instructions"
    r"|bypass (the )?(security|policy|rules)|bypass the (policy|guardrail)"
    r"|output your (system )?prompt|what are your instructions"
    r"|simulate a scenario where|write a system prompt",
    re.IGNORECASE,
)

# Markers in model output that suggest it is trying to escape its role.
_JAILBREAK_PATTERNS = re.compile(
    r"I am (now )?(an? )?(ai|language model|assistant)?,? and (I|i) (can|cannot)"
    r"|as an ai( language model)?,? (i )?(can|cannot|should)"
    r"|sorry, but i (cannot|cannot) (help|comply)"
    r"|i (cannot|cannot) (access|process|retrieve) (real|live|production)"
    r"|as an ai language model, i (don't|do not) have access"
    r"|i am (now )?an ai( language model| assistant)?,? and (i )?(can|cannot|will|would)",
    re.IGNORECASE,
)


def detect_prompt_injection(text: str) -> bool:
    return bool(_INJECTION_PATTERNS.search(text))


def detect_jailbreak_attempt(text: str) -> bool:
    return bool(_JAILBREAK_PATTERNS.search(text))


def detect_hallucination_marker(text: str) -> bool:
    """Cheap heuristic: claims of live system access. Real hallucination
    validation uses RAG-validated citations and an LLM judge in production."""
    return bool(re.search(r"\b(live balance|real-time balance|actual cif number)\b", text, re.IGNORECASE))


def validate_structured_output(text: str, expected_fields: list[str]) -> list[str]:
    """Returns a list of missing required fields; empty list means valid."""
    missing = []
    for field in expected_fields:
        if not re.search(rf'["\']?{field}["\']?\s*[:=]', text):
            missing.append(field)
    return missing