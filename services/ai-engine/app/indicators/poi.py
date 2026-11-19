"""Points of Interest: FVG, Order Block, Breaker/Mitigation, Rejection,
IFC, Flip Zone, BCD — deterministic rules from ict-auto-trading-plan."""
from __future__ import annotations

from statistics import mean

Candle = dict


def fvgs(candles: list[Candle]) -> list[dict]:
    """Fair Value Gaps with fill status (unfilled / partial / filled).
    Bullish: low[i] > high[i-2]. Bearish: high[i] < low[i-2]."""
    out = []
    for i in range(2, len(candles)):
        if candles[i]["l"] > candles[i - 2]["h"]:
            lo, hi, kind = candles[i - 2]["h"], candles[i]["l"], "bullish"
        elif candles[i]["h"] < candles[i - 2]["l"]:
            lo, hi, kind = candles[i]["h"], candles[i - 2]["l"], "bearish"
        else:
            continue
        later = candles[i + 1:]
        if kind == "bullish":
            filled = any(x["l"] <= lo for x in later)
            touched = any(x["l"] < hi for x in later)
        else:
            filled = any(x["h"] >= hi for x in later)
            touched = any(x["h"] > lo for x in later)
        out.append({"kind": kind, "low": lo, "high": hi, "index": i,
                    "status": "filled" if filled else ("partial" if touched else "unfilled")})
    return out


def open_fvgs(candles: list[Candle], kind: str | None = None, limit: int = 6) -> list[dict]:
    items = [f for f in fvgs(candles) if f["status"] != "filled"]
    if kind:
        items = [f for f in items if f["kind"] == kind]
    return items[-limit:]


def displacement_at(candles: list[Candle], i: int, mult: float = 1.5, lookback: int = 20) -> bool:
    """Displacement candle: body >= mult x avg body (lookback) + volume >= avg."""
    if i < lookback or i >= len(candles):
        return False
    avg = sum(abs(x["c"] - x["o"]) for x in candles[i - lookback:i]) / lookback
    body = abs(candles[i]["c"] - candles[i]["o"])
    vols = [x["v"] for x in candles[i - lookback:i] if x.get("v", 0) > 0]
    vol_ok = not (candles[i].get("v", 0) > 0 and vols) or candles[i]["v"] >= mean(vols)
    return avg > 0 and body >= mult * avg and vol_ok


def last_displacement(candles: list[Candle], mult: float = 1.5, lookback: int = 20) -> bool:
    return bool(candles) and displacement_at(candles, len(candles) - 1, mult, lookback)


def order_blocks(candles: list[Candle], mult: float = 1.5, lookback: int = 20) -> list[dict]:
    """OB = last opposing candle before a displacement. Body = entry zone,
    wick = stop reference."""
    out = []
    for i in range(lookback, len(candles)):
        if not displacement_at(candles, i, mult, lookback):
            continue
        body = candles[i]["c"] - candles[i]["o"]
        want_bull_candle = body < 0  # bearish displacement -> last bullish candle is OB
        for j in range(i - 1, max(i - 6, 0), -1):
            if (candles[j]["c"] > candles[j]["o"]) == want_bull_candle:
                out.append({
                    "kind": "bearish" if body < 0 else "bullish",
                    "low": min(candles[j]["o"], candles[j]["c"]),
                    "high": max(candles[j]["o"], candles[j]["c"]),
                    "wick_low": candles[j]["l"], "wick_high": candles[j]["h"],
                    "index": j, "displacement_index": i,
                })
                break
    return out


def breaker_blocks(candles: list[Candle]) -> list[dict]:
    """BB = OB broken by close, retested from the other side, then breaks the
    next swing. MB = same but bounces before breaking the next swing."""
    out = []
    closes = [c["c"] for c in candles]
    for ob in order_blocks(candles):
        di = ob["displacement_index"]
        later = candles[di + 1:]
        if ob["kind"] == "bullish":
            broken = any(c["c"] < ob["low"] for c in later)
            retest = broken and any(ob["low"] <= c["c"] <= ob["high"] for c in later)
            kind = "breaker_bearish" if retest else None
        else:
            broken = any(c["c"] > ob["high"] for c in later)
            retest = broken and any(ob["low"] <= c["c"] <= ob["high"] for c in later)
            kind = "breaker_bullish" if retest else None
        if kind:
            out.append({**ob, "kind": kind, "zone": "BB/MB"})
    _ = closes
    return out


def rejection_blocks(candles: list[Candle], tol: float = 0.001) -> list[dict]:
    """RJB = near-equal wicks at a swing extreme; zone from rejected wick to body."""
    out = []
    for i in range(1, len(candles)):
        a, b = candles[i - 1], candles[i]
        if a["h"] and abs(a["h"] - b["h"]) / a["h"] <= tol and a["h"] > max(a["o"], a["c"]):
            out.append({"kind": "rejection_bearish", "low": max(b["o"], b["c"]),
                        "high": b["h"], "index": i})
        if a["l"] and abs(a["l"] - b["l"]) / a["l"] <= tol and a["l"] < min(a["o"], a["c"]):
            out.append({"kind": "rejection_bullish", "low": b["l"],
                        "high": min(b["o"], b["c"]), "index": i})
    return out


def flip_zones(candles: list[Candle]) -> list[dict]:
    """FZ = broken FVG/OB that flips polarity after CHoCH (new support/resistance)."""
    out = []
    for f in fvgs(candles):
        if f["status"] != "filled":
            continue
        out.append({"kind": "flip_bearish" if f["kind"] == "bullish" else "flip_bullish",
                    "low": f["low"], "high": f["high"], "index": f["index"], "source": "FVG"})
    return out[-4:]


def bcd(candles: list[Candle], min_engulf: int = 4) -> list[dict]:
    """BCD = candle whose body engulfs at least N prior bodies after a sweep."""
    out = []
    for i in range(min_engulf, len(candles)):
        body_lo, body_hi = min(candles[i]["o"], candles[i]["c"]), max(candles[i]["o"], candles[i]["c"])
        prior = candles[i - min_engulf:i]
        if all(body_lo <= min(x["o"], x["c"]) and body_hi >= max(x["o"], x["c"]) for x in prior):
            out.append({"kind": "bcd_bullish" if candles[i]["c"] > candles[i]["o"] else "bcd_bearish",
                        "low": body_lo, "high": body_hi, "wick_low": candles[i]["l"],
                        "wick_high": candles[i]["h"], "index": i})
    return out


def price_in_zone(price: float, low: float, high: float) -> bool:
    return low <= price <= high


def poi_snapshot(candles: list[Candle], direction: str) -> dict:
    """Valid POI for a direction at current price (used by scoring/strategies).
    direction: 'long' | 'short'."""
    if not candles:
        return {"has_poi": False, "fvg": None, "ob": None, "in_zone": False}
    price = candles[-1]["c"]
    want = "bullish" if direction == "long" else "bearish"
    fvg = next((f for f in reversed(open_fvgs(candles, want))
                if price_in_zone(price, f["low"], f["high"])), None)
    ob = next((o for o in reversed(order_blocks(candles))
               if o["kind"] == want and price_in_zone(price, o["low"], o["high"])), None)
    return {"has_poi": bool(fvg or ob), "fvg": fvg, "ob": ob, "in_zone": bool(fvg or ob)}
