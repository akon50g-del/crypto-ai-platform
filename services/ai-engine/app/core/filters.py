"""Mandatory filters — any failure means NO signal (STRATEGY_SPEC §7).
Enrichment (Nansen / liquidations) confirms only; it never enters the score."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def check_filters(*, side: str, strategy: str, final_rr: float, min_final_rr: float,
                  htf_bias: str, btc_bias: str | None, btc_context_enabled: bool,
                  atr_anomaly: bool, has_active_signal: bool,
                  news_events: list[dict] | None = None,
                  news_blackout_minutes: int = 30,
                  now: datetime | None = None) -> dict:
    """Returns {passed: bool, failures: [str]}. `news_events` items need
    `scheduled_at` (datetime) + `impact` ('HIGH' blocks)."""
    failures: list[str] = []
    if final_rr < min_final_rr:
        failures.append(f"final RR {final_rr} < {min_final_rr}")
    # Timeframe alignment: no 15m long into clear 4H downtrend except reversal paths (B / method 2)
    if strategy not in ("B",):
        if side == "long" and htf_bias == "bearish":
            failures.append("long against bearish 4H bias")
        if side == "short" and htf_bias == "bullish":
            failures.append("short against bullish 4H bias")
    if btc_context_enabled and btc_bias:
        if side == "long" and btc_bias == "bearish":
            failures.append("long against sharp bearish BTC 4H structure")
        if side == "short" and btc_bias == "bullish":
            failures.append("short against sharp bullish BTC 4H structure")
    if atr_anomaly:
        failures.append("anomalous ATR / volatility spike")
    if has_active_signal:
        failures.append("active signal already exists for symbol")
    now = now or datetime.now(timezone.utc)
    for ev in news_events or []:
        when = ev.get("scheduled_at")
        if when and str(ev.get("impact", "")).upper() == "HIGH":
            if abs((when - now).total_seconds()) <= news_blackout_minutes * 60:
                failures.append(f"high-impact news blackout: {ev.get('title', 'event')}")
                break
    return {"passed": not failures, "failures": failures}


def correlation_guard(active_sides: list[str], new_side: str, max_correlated: int = 2) -> bool:
    """At most N correlated signals in the same direction vs BTC."""
    return sum(1 for s in active_sides if s == new_side) < max_correlated


def news_window(now: datetime, minutes: int) -> tuple[datetime, datetime]:
    return now - timedelta(minutes=minutes), now + timedelta(minutes=minutes)
