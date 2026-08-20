"""Deterministic loan eligibility engine. NEVER trusts LLM output — this is the
authority for eligibility decisions. Returns an explainable decision with
per-rule evidence so the supervisor agent can narrate it to the customer."""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Deterministic thresholds (configurable per institution).
MIN_SCORE = 550
MIN_ANNUAL_INCOME = 300_000
MAX_EMI_TO_INCOME = 0.45


@dataclass
class RuleResult:
    rule: str
    passed: bool
    detail: str


@dataclass
class EligibilityDecision:
    eligible: bool
    score: int
    max_amount: int
    reasons: list[RuleResult]
    policy_version: str

    def to_dict(self) -> dict:
        return {"policy_version": self.policy_version, **asdict(self)}


def assess_eligibility(
    *,
    income: float,
    cibil_score: int,
    existing_emis: float,
    requested_amount: float,
    tenure_months: int,
    debt_to_income: float | None = None,
) -> EligibilityDecision:
    reasons: list[RuleResult] = []

    credit_ok = cibil_score >= MIN_SCORE
    reasons.append(RuleResult("min_cibil", credit_ok, f"CIBIL {cibil_score} >= {MIN_SCORE}"))

    income_ok = income >= MIN_ANNUAL_INCOME
    reasons.append(RuleResult("min_income", income_ok, f"income {income} >= {MIN_ANNUAL_INCOME}"))

    # EMI capacity check
    monthly_income = income / 12
    if tenure_months > 0 and monthly_income > 0:
        est_emi = requested_amount / tenure_months  # placeholder: flat EMI
        obli_ratio = (existing_emis + est_emi) / monthly_income
        capacity_ok = obli_ratio <= MAX_EMI_TO_INCOME
        reasons.append(
            RuleResult(
                "obligation_ratio",
                capacity_ok,
                f"projected obligation ratio {obli_ratio:.2f} <= {MAX_EMI_TO_INCOME}",
            )
        )
    else:
        capacity_ok = False
        reasons.append(RuleResult("obligation_ratio", False, "invalid tenure or income"))

    dti = debt_to_income if debt_to_income is not None else (existing_emis * 12 / income if income else 1.0)
    dti_ok = dti <= 0.55
    reasons.append(RuleResult("debt_to_income", dti_ok, f"DTI {dti:.2f} <= 0.55"))

    # Weighted score (deterministic, explainable)
    score = 300
    score += min(250, cibil_score // 2)
    score += 150 if income >= 1_000_000 else (100 if income >= 500_000 else 50)
    score -= int((dti * 100) / 2) if dti_ok else 80
    score = max(0, min(900, score))

    eligible = credit_ok and income_ok and capacity_ok and dti_ok
    max_amount = int(monthly_income * MAX_EMI_TO_INCOME * tenure_months) if eligible else 0

    return EligibilityDecision(
        eligible=eligible,
        score=score,
        max_amount=max_amount,
        reasons=reasons,
        policy_version="eligibility-v1",
    )