"""Classic technicals (EMA/SMA/ATR/ADX) — pure Python, TA-Lib if available.

TA-Lib is optional: if installed we use it, otherwise identical pure-Python
implementations (ported from backtest_ict.py) keep the engine portable.
"""
from __future__ import annotations

import statistics

try:  # pragma: no cover - depends on environment
    import talib  # type: ignore
    HAS_TALIB = True
except Exception:  # pragma: no cover
    talib = None
    HAS_TALIB = False

Candle = dict


def sma(values: list[float], n: int) -> float | None:
    return sum(values[-n:]) / n if len(values) >= n else None


def ema(values: list[float], n: int) -> float | None:
    if len(values) < n:
        return None
    if HAS_TALIB:
        import numpy as np
        out = talib.EMA(np.array(values, dtype=float), timeperiod=n)
        return float(out[-1]) if len(out) and out[-1] == out[-1] else None
    value = sum(values[:n]) / n
    alpha = 2 / (n + 1)
    for x in values[n:]:
        value = alpha * x + (1 - alpha) * value
    return value


def atr(candles: list[Candle], n: int = 14) -> float | None:
    if len(candles) < n + 1:
        return None
    if HAS_TALIB:
        import numpy as np
        out = talib.ATR(
            np.array([c["h"] for c in candles], dtype=float),
            np.array([c["l"] for c in candles], dtype=float),
            np.array([c["c"] for c in candles], dtype=float), timeperiod=n)
        return float(out[-1]) if len(out) and out[-1] == out[-1] else None
    trs = [max(candles[i]["h"] - candles[i]["l"],
               abs(candles[i]["h"] - candles[i - 1]["c"]),
               abs(candles[i]["l"] - candles[i - 1]["c"]))
           for i in range(1, len(candles))]
    return sum(trs[-n:]) / n


def adx(candles: list[Candle], n: int = 14) -> float | None:
    if len(candles) < 2 * n + 1:
        return None
    if HAS_TALIB:
        import numpy as np
        out = talib.ADX(
            np.array([c["h"] for c in candles], dtype=float),
            np.array([c["l"] for c in candles], dtype=float),
            np.array([c["c"] for c in candles], dtype=float), timeperiod=n)
        return float(out[-1]) if len(out) and out[-1] == out[-1] else None
    trs, plus, minus = [], [], []
    for i in range(1, len(candles)):
        up = candles[i]["h"] - candles[i - 1]["h"]
        down = candles[i - 1]["l"] - candles[i]["l"]
        trs.append(max(candles[i]["h"] - candles[i]["l"],
                       abs(candles[i]["h"] - candles[i - 1]["c"]),
                       abs(candles[i]["l"] - candles[i - 1]["c"])))
        plus.append(up if up > down and up > 0 else 0.0)
        minus.append(down if down > up and down > 0 else 0.0)
    dx = []
    for i in range(n - 1, len(trs)):
        tr = sum(trs[i - n + 1:i + 1])
        if tr <= 0:
            continue
        pdi = 100 * sum(plus[i - n + 1:i + 1]) / tr
        mdi = 100 * sum(minus[i - n + 1:i + 1]) / tr
        dx.append(100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi else 0)
    return sum(dx[-n:]) / n if len(dx) >= n else None


def regime(candles: list[Candle], swing_n: int = 2) -> str:
    """Market regime: bull_trend / bear_trend / range / high_vol_range."""
    from app.indicators.structure import swings
    sh, sl = swings(candles, swing_n)
    if len(sh) >= 2 and len(sl) >= 2:
        if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
            return "bull_trend"
        if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
            return "bear_trend"
    ranges = [x["h"] - x["l"] for x in candles[-20:]]
    if not ranges:
        return "unknown"
    med = statistics.median(ranges)
    return "high_vol_range" if med and ranges[-1] > 1.5 * med else "range"


def atr_anomalous(candles: list[Candle], n: int = 14, factor: float = 3.0) -> bool:
    """Volatility filter: latest true range wildly above ATR (news spike)."""
    a = atr(candles, n)
    if a is None or len(candles) < 2 or a <= 0:
        return False
    last_tr = max(candles[-1]["h"] - candles[-1]["l"],
                  abs(candles[-1]["h"] - candles[-2]["c"]),
                  abs(candles[-1]["l"] - candles[-2]["c"]))
    return last_tr > factor * a


def volume_ok(candles: list[Candle], i: int, n: int = 20) -> bool:
    vals = [x["v"] for x in candles[i - n:i] if x.get("v", 0) > 0]
    return not vals or candles[i].get("v", 0) >= statistics.mean(vals)
