"""PII detection and masking/redaction for logs, traces, and LLM prompts.

Every log line and trace should go through these helpers so that PII never
leaks to the observability stack. This is a central redaction point — never
log raw request bodies.
"""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_FIELDS = frozenset(
    {
        "pan",
        "aadhaar",
        "ssn",
        "card_number",
        "cvv",
        "cvv2",
        "pin",
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "account_number",
        "iban",
        "dob",
        "email",
        "phone",
        "phone_number",
        "otp",
        "secret",
    }
)

# Heuristic detectors (masked in free text even when the field name is unknown).
_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b")

_MASKS: dict[str, str] = {
    "pan": "PANXXXX9999",
    "aadhaar": "XXXX-XXXX-XXXX",
    "ssn": "XXX-XX-XXXX",
    "card_number": "************9999",
    "cvv": "***",
    "pin": "***",
    "password": "***",
    "account_number": "*****9999",
    "iban": "IBAN***",
    "email": "***@***",
    "phone": "******XXXX",
    "otp": "***",
}


def mask_field(field_name: str, value: Any) -> Any:
    """Mask a single field value based on its name."""
    key = field_name.lower()
    if key in _MASKS:
        return _MASKS[key]
    if "token" in key or "secret" in key or "key" in key or "password" in key:
        return "***"
    return value


def mask_text(text: str) -> str:
    """Redact heuristic PII patterns from free text."""
    masked = _PAN_RE.sub("PANXXXX9999", text)
    masked = _EMAIL_RE.sub("***@***", masked)
    masked = _PHONE_RE.sub("******XXXX", masked)
    masked = _CARD_RE.sub("*****", masked)
    return masked


def mask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask sensitive keys in a JSON-like payload."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        k = key.lower()
        if k in SENSITIVE_FIELDS or "token" in k or "secret" in k or "key" in k:
            out[key] = mask_field(key, value)
        elif isinstance(value, dict):
            out[key] = mask_payload(value)
        elif isinstance(value, list):
            out[key] = [mask_payload(v) if isinstance(v, dict) else v for v in value]
        else:
            out[key] = mask_text(str(value)) if isinstance(value, str) else value
    return out