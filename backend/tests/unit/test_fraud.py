"""Unit tests for the deterministic fraud engine."""

from app.decisioning.fraud import score_transaction


def test_low_risk_approve():
    d = score_transaction(
        amount=2000,
        velocity_24h=1,
        ip_new=False,
        device_new=False,
        amount_vs_avg=0.8,
        country_mismatch=False,
    )
    assert d.verdict == "approve"
    assert d.risk_score < 50


def test_high_risk_block():
    d = score_transaction(
        amount=900_000,
        velocity_24h=15,
        ip_new=True,
        device_new=True,
        amount_vs_avg=8.0,
        country_mismatch=True,
    )
    assert d.verdict == "block"
    assert d.risk_score >= 80


def test_medium_risk_review():
    d = score_transaction(
        amount=700_000,
        velocity_24h=12,
        ip_new=True,
        device_new=True,
        amount_vs_avg=5.0,
        country_mismatch=False,
    )
    assert d.verdict == "review"
    assert 50 <= d.risk_score < 80


def test_explainable_signals():
    d = score_transaction(
        amount=2000,
        velocity_24h=1,
        ip_new=False,
        device_new=False,
        amount_vs_avg=0.8,
        country_mismatch=False,
    )
    assert len(d.signals) == 6
    assert d.model_version == "fraud-v1"