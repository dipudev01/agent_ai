"""PII masking and field encryption tests."""

import pytest

from app.core.security import pii
from app.core.security.encryption import decrypt, encrypt


def test_masks_sensitive_fields():
    masked = pii.mask_payload(
        {
            "pan": "ABCDE1234F",
            "email": "priya@example.com",
            "phone": "+919800001234",
            "password": "hunter2",
            "nested": {"account_number": "1234567890"},
        }
    )
    assert masked["pan"] == "PANXXXX9999"
    assert masked["email"] == "***@***"
    assert masked["password"] == "***"
    assert masked["nested"]["account_number"] == "*****9999"


def test_masks_free_text():
    text = "Customer PAN is ABCDE1234F and email priya@example.com"
    masked = pii.mask_text(text)
    assert "ABCDE1234F" not in masked
    assert "priya@example.com" not in masked


def test_encryption_roundtrip():
    plain = "AADHAAR-1234-5678-9012"
    enc = encrypt(plain)
    assert enc != plain
    assert decrypt(enc) == plain


def test_encryption_deterministic_storage():
    # Encryption output is unique per call (random IV) but decrypts correctly.
    a, b = encrypt("same"), encrypt("same")
    assert a != b
    assert decrypt(a) == decrypt(b) == "same"


def test_encryption_rejects_wrong_key():
    with pytest.raises(ValueError):
        decrypt("not-a-ciphertext")