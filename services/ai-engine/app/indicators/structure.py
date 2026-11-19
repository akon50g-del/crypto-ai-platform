"""ICT structure engine — pure functions over CLOSED candles only.

Candle format everywhere in the engine: dict with keys
  t (epoch ms or ISO str), o, h, l, c, v  — oldest first.
Ported from ict_analyze.py / backtest_ict.py in the original Skills.
"""
from __future__ import annotations

Candle = dict


def swings(candles: list[Candle], n: int = 2) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Swing highs/lows. A swing at i is only confirmed after candle i+n closes
    (no look-ahead)."""
    hi, lo = [], []
    for i in range(n, len(candles) - n):
        if all(candles[i]["h"] > candles[i - k]["h"] and candles[i]["h"] > candles[i + k]["h"]
               for k in range(1, n + 1)):
            hi.append((i, candles[i]["h"]))
        if all(candles[i]["l"] < candles[i - k]["l"] and candles[i]["l"] < candles[i + k]["l"]
               for k in range(1, n + 1)):
            lo.append((i, candles[i]["l"]))
    return hi, lo


def bias(candles: list[Candle], n: int = 2) -> str:
    """HTF bias from last two swing highs/lows: HH+HL bullish, LH+LL bearish."""
    sh, sl = swings(candles, n)
    if len(sh) >= 2 and len(sl) >= 2:
        if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
            return "bullish"
        if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
            return "bearish"
    return "range"


def last_leg(candles: list[Candle], n: int = 2,
             ote_low: float = 0.62, ote_high: float = 0.79) -> dict | None:
    """Last swing-to-swing leg with OTE zone and equilibrium (50%)."""
    sh, sl = swings(candles, n)
    if not sh or not sl:
        return None
    (ih, ph), (il, pl) = sh[-1], sl[-1]
    rng = ph - pl
    if rng <= 0:
        return None
    if il > ih:  # last leg down -> retrace up into premium, look to sell
        return {"direction": "down", "high": ph, "low": pl,
                "ote_low": pl + ote_low * rng, "ote_high": pl + ote_high * rng,
                "eq": pl + 0.5 * rng}
    return {"direction": "up", "high": ph, "low": pl,
            "ote_low": ph - ote_high * rng, "ote_high": ph - ote_low * rng,
            "eq": ph - 0.5 * rng}


def equal_levels(points: list[tuple[int, float]], tol: float = 0.0015) -> list[float]:
    """Equal highs/lows (pooled liquidity) within tolerance."""
    out = []
    for a in range(len(points)):
        for b in range(a + 1, len(points)):
            if points[a][1] and abs(points[a][1] - points[b][1]) / points[a][1] <= tol:
                out.append(round((points[a][1] + points[b][1]) / 2, 8))
    return sorted(set(out))


def liquidity_pools(candles: list[Candle], n: int = 2) -> dict:
    """BSL above price / SSL below price from swing points."""
    if not candles:
        return {"bsl_above": [], "ssl_below": [], "equal_highs": [], "equal_lows": []}
    price = candles[-1]["c"]
    sh, sl = swings(candles, n)
    return {
        "bsl_above": sorted(p for _, p in sh if p > price)[:4],
        "ssl_below": sorted((p for _, p in sl if p < price), reverse=True)[:4],
        "equal_highs": equal_levels(sh),
        "equal_lows": equal_levels(sl),
        "last_swing_highs": [p for _, p in sh[-3:]],
        "last_swing_lows": [p for _, p in sl[-3:]],
    }


def bos(candles: list[Candle], direction: str, n: int = 2) -> bool:
    """Break of Structure: last close breaks last swing in trend direction."""
    if not candles:
        return False
    sh, sl = swings(candles, n)
    last_close = candles[-1]["c"]
    if direction == "long" and sh:
        return last_close > sh[-1][1]
    if direction == "short" and sl:
        return last_close < sl[-1][1]
    return False


def choch(candles: list[Candle], direction: str, n: int = 2) -> bool:
    """Change of Character / MSS: close breaks the opposing swing.
    `direction` is the NEW direction after the shift."""
    if not candles:
        return False
    sh, sl = swings(candles, n)
    last_close = candles[-1]["c"]
    if direction == "long" and sh:   # was bearish, close above last swing high
        return last_close > sh[-1][1]
    if direction == "short" and sl:  # was bullish, close below last swing low
        return last_close < sl[-1][1]
    return False


def inducement(candles: list[Candle], n: int = 2) -> dict:
    """IDM = last internal swing before the main swing. Swept when price wicks
    beyond it and closes back inside."""
    sh, sl = swings(candles, n)
    result = {"idm_high": None, "idm_low": None, "idm_high_swept": False, "idm_low_swept": False}
    if len(sh) >= 2:
        result["idm_high"] = sh[-2][1]
    if len(sl) >= 2:
        result["idm_low"] = sl[-2][1]
    if candles:
        last = candles[-1]
        if result["idm_high"] is not None:
            result["idm_high_swept"] = last["h"] > result["idm_high"] and last["c"] < result["idm_high"]
        if result["idm_low"] is not None:
            result["idm_low_swept"] = last["l"] < result["idm_low"] and last["c"] > result["idm_low"]
    return result


def sweep(candles: list[Candle], direction: str, n: int = 2) -> bool:
    """Liquidity sweep on the last closed candle in the trade direction:
    long = wick below prior swing low + close back above it (and vice versa)."""
    if len(candles) < n + 2:
        return False
    sh, sl = swings(candles, n)
    last = candles[-1]
    if direction == "long":
        prior = [p for i, p in sl if i < len(candles) - 1]
        return bool(prior and last["l"] < min(prior) and last["c"] > min(prior))
    prior = [p for i, p in sh if i < len(candles) - 1]
    return bool(prior and last["h"] > max(prior) and last["c"] < max(prior))


def premium_discount(candles: list[Candle], n: int = 2) -> str:
    """Where price sits in the last leg: premium (sell zone) / discount (buy)."""
    leg = last_leg(candles, n)
    if not leg or not candles:
        return "unknown"
    return "premium" if candles[-1]["c"] > leg["eq"] else "discount"
