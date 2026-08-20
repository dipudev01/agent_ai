"""Field-level encryption (Fernet) for sensitive columns and payload fields.

Used for PII fields stored at rest (e.g. PAN, DOB, account numbers) as a
defense-in-depth layer on top of disk encryption. Keys are expected to come
from KMS in production and are base64-encoded Fernet keys.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        raw = settings.encryption_key.encode()
        if len(raw) != 44:
            # Derive a stable 32-byte key from the configured secret.
            raw = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
        _fernet = Fernet(raw)
    return _fernet


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("failed to decrypt field") from exc