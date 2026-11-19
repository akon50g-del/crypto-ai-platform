"""Risk engine — position sizing ported from position_size.py.

qty = (balance x risk%) / |entry - sl| · notional = qty x entry · margin = notional / leverage
PnL figures are BEFORE fees/slippage (stated explicitly in UI copy).
"""
from __future__ import annotations


def position_size(balance: float, risk_pct: float, entry: float, sl: float,
                  targets: list[float] | None = None, leverage: float = 3.0) -> dict:
    dist = abs(entry - sl)
    if dist == 0:
        raise ValueError("entry and sl must differ")
    side = "short" if sl > entry else "long"
    risk_amt = balance * risk_pct / 100
    qty = risk_amt / dist
    notional = qty * entry
    out = {
        "side": side, "risk_amount": round(risk_amt, 4),
        "sl_distance": round(dist, 6), "sl_distance_pct": round(dist / entry * 100, 3),
        "qty": round(qty, 6), "notional": round(notional, 2),
        "margin_at_leverage": round(notional / leverage, 2),
        "leverage": leverage, "notional_vs_balance": round(notional / balance, 2) if balance else None,
        "targets": [],
    }
    for t in targets or []:
        reward = (entry - t) if side == "short" else (t - entry)
        out["targets"].append({"price": t, "pnl": round(reward * qty, 2),
                                "rr": round(reward / dist, 2)})
    if balance and risk_amt / balance > 0.02:
        out["warning"] = "risk above 2% of balance"
    return out


def rr(entry: float, sl: float, tp: float) -> float:
    risk = abs(entry - sl)
    return round(abs(tp - entry) / risk, 2) if risk else 0.0


def weighted_rr(entry: float, sl: float, tp1: float, tp2: float, partial: float = 0.5) -> float:
    """Weighted RR across partial TP1 + remainder TP2 (final-RR gate uses this
    or TP2 alone, per spec: TP1 may be < 1:2 since only part closes there)."""
    return round(partial * rr(entry, sl, tp1) + (1 - partial) * rr(entry, sl, tp2), 2)


def stop_loss(side: str, origin: float, atr_value: float | None,
              buffer_atr: tuple[float, float] = (0.1, 0.2)) -> float:
    """SL beyond the origin (OB/leg/sweep extreme) + 0.1-0.2 x ATR buffer."""
    buf = (atr_value or 0) * ((buffer_atr[0] + buffer_atr[1]) / 2)
    return origin + buf if side == "short" else origin - buf


def targets_from_liquidity(side: str, entry: float, sl: float,
                           bsl_above: list[float], ssl_below: list[float],
                           tp2_r: float = 2.5) -> tuple[float, float, bool]:
    """TP1 = nearest real liquidity; TP2 = next liquidity or tp2_r fallback.
    Returns (tp1, tp2, tp_is_structural). Psychological numbers are NOT
    structural targets — the fallback is flagged as such."""
    risk = abs(entry - sl)
    if side == "long":
        pool = [p for p in bsl_above if p > entry]
        tp1 = pool[0] if pool else entry + 1.25 * risk
        tp2 = pool[1] if len(pool) > 1 else entry + tp2_r * risk
        return tp1, max(tp2, entry + tp2_r * risk) if len(pool) <= 1 else tp2, bool(pool)
    pool = [p for p in ssl_below if p < entry]
    tp1 = pool[0] if pool else entry - 1.25 * risk
    tp2 = pool[1] if len(pool) > 1 else entry - tp2_r * risk
    return tp1, min(tp2, entry - tp2_r * risk) if len(pool) <= 1 else tp2, bool(pool)
