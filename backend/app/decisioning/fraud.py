"""Deterministic fraud risk scoring. Combines feature-store signals into a risk
score with explainable contributions. Output feeds the Fraud Engine policy —
never the LLM. High-risk outcomes require human review (HITL)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Signal:
    name: str
    weight: float
    value: float
    detail: str

    @property
    def contribution(self) -> float:
        return self.weight * self.value


@dataclass
class FraudDecision:
    risk_score: float
    verdict: str  # approve | review | block
    signals: list[Signal]
    model_version: str

    def to_dict(self) -> dict:
        return {"model_version": self.model_version, **asdict(self)}


def score_transaction(
    *,
    amount: float,
    velocity_24h: int,
    ip_new: bool,
    device_new: bool,
    amount_vs_avg: float,
    country_mismatch: bool,
) -> FraudDecision:
    signals = [
        Signal("amount", 0.30, min(1.0, amount / 1_000_000), f"amount {amount}"),
        Signal("velocity_24h", 0.20, min(1.0, velocity_24h / 20), f"{velocity_24h} txn/24h"),
        Signal("ip_new", 0.10, 1.0 if ip_new else 0.0, "new IP address"),
        Signal("device_new", 0.15, 1.0 if device_new else 0.0, "new device"),
        Signal("amount_vs_avg", 0.15, min(1.0, amount_vs_avg / 5.0), f"{amount_vs_avg:.1f}x average"),
        Signal("country_mismatch", 0.10, 1.0 if country_mismatch else 0.0, "country mismatch"),
    ]
    risk = round(sum(s.contribution for s in signals) * 100, 2)

    if risk >= 80:
        verdict = "block"
    elif risk >= 50:
        verdict = "review"
    else:
        verdict = "approve"

    return FraudDecision(risk_score=risk, verdict=verdict, signals=signals, model_version="fraud-v1")