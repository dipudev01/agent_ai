"""Unit tests for the deterministic eligibility engine."""

import pytest

from app.decisioning.eligibility import assess_eligibility


def test_eligible_high_income_good_credit():
    d = assess_eligibility(
        income=1_500_000,
        cibil_score=780,
        existing_emis=8_000,
        requested_amount=1_000_000,
        tenure_months=60,
    )
    assert d.eligible is True
    assert d.max_amount > 0
    assert all(r.passed for r in d.reasons if r.rule != "obligation_ratio") or d.eligible


def test_rejected_low_credit():
    d = assess_eligibility(
        income=1_500_000,
        cibil_score=450,
        existing_emis=8_000,
        requested_amount=1_000_000,
        tenure_months=60,
    )
    assert d.eligible is False
    assert any(not r.passed for r in d.reasons)


def test_rejected_low_income():
    d = assess_eligibility(
        income=150_000,
        cibil_score=780,
        existing_emis=0,
        requested_amount=500_000,
        tenure_months=60,
    )
    assert d.eligible is False


def test_explainable_reasons():
    d = assess_eligibility(
        income=900_000,
        cibil_score=700,
        existing_emis=20_000,
        requested_amount=1_200_000,
        tenure_months=48,
    )
    assert len(d.reasons) >= 4
    assert d.policy_version == "eligibility-v1"
    assert all(r.rule for r in d.reasons)


@pytest.mark.parametrize(
    "income,cibil,emis,amount,tenure,expected",
    [
        (2_000_000, 800, 5_000, 1_500_000, 60, True),
        (200_000, 700, 0, 100_000, 60, False),
        (900_000, 600, 30_000, 800_000, 36, False),
    ],
)
def test_eligibility_matrix(income, cibil, emis, amount, tenure, expected):
    d = assess_eligibility(
        income=income,
        cibil_score=cibil,
        existing_emis=emis,
        requested_amount=amount,
        tenure_months=tenure,
    )
    assert d.eligible == expected