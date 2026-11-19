"""Unified acceptance score /10 — one system for all strategies (STRATEGY_SPEC §6).

bias 2 · poi 2 · sweep 1 · mss 2 · ltf 1 · liquidity target 1 · RR 1
Execute >= 7 (A / A+), watch 5-6, reject < 5. Touching a zone is NOT an entry.
"""
from __future__ import annotations


def compute_score(*, bias_clear: bool, poi_valid: bool, swept: bool, mss: bool,
                  ltf_confirmed: bool, liquidity_target: bool, rr_ok: bool,
                  weights: dict | None = None) -> dict:
    w = weights or {"bias": 2, "poi": 2, "sweep": 1, "mss": 2,
                    "ltfConfirmation": 1, "liquidityTarget": 1, "rr": 1}
    breakdown = {
        "bias": w["bias"] if bias_clear else 0,
        "poi": w["poi"] if poi_valid else 0,
        "sweep": w["sweep"] if swept else 0,
        "mss": w["mss"] if mss else 0,
        "ltfConfirmation": w["ltfConfirmation"] if ltf_confirmed else 0,
        "liquidityTarget": w["liquidityTarget"] if liquidity_target else 0,
        "rr": w["rr"] if rr_ok else 0,
    }
    score = sum(breakdown.values())
    grade = "A+" if score >= 8 else ("A" if score >= 7 else ("WATCH" if score >= 5 else "REJECTED"))
    status = "READY" if score >= 7 else ("WATCH" if score >= 5 else "NO_SETUP")
    return {"score": score, "breakdown": breakdown, "grade": grade, "status": status}
