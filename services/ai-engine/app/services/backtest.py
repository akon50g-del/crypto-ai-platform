"""Conservative walk-forward backtester — ported from backtest_ict.py.

Signals use only candles before the decision candle. SL-first when SL and TP
touch in the same candle. Partial TP1 -> break-even -> TP2. Fees/slippage in R.
Acceptance (STRATEGY_SPEC §11): >=100 closed trades, PF >= 1.20, positive
expectancy & Net R after costs, acceptable drawdown, OOS pass.
"""
from __future__ import annotations

from app.indicators import structure as st
from app.indicators.poi import displacement_at
from app.indicators.technicals import regime as regime_of
from app.strategies.strategy_c_breakout_retest import breakout_setup
from app.strategies.strategy_d_mean_reversion import mean_reversion_setup


def _ict_setup(candles: list[dict], mode: str, require_volume: bool = False) -> dict | None:
    sh, sl = st.swings(candles)
    if len(sh) < 2 or len(sl) < 2:
        return None
    if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
        bias = "long"
    elif sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
        bias = "short"
    else:
        return None
    leg = st.last_leg(candles)
    if not leg:
        return None
    lo, hi = leg["ote_low"], leg["ote_high"]
    bar = candles[-1]
    touched = bar["l"] <= hi and bar["h"] >= lo
    rejected = (bias == "short" and bar["c"] < lo) or (bias == "long" and bar["c"] > hi)
    from app.indicators.poi import poi_snapshot
    poi = poi_snapshot(candles, bias)
    mss = st.choch(candles, bias) and displacement_at(candles, len(candles) - 1)
    swept = st.sweep(candles, bias)
    score = 1 + int(poi["has_poi"]) + int(touched) + int(mss) + int(swept)
    if require_volume and not displacement_at(candles, len(candles) - 1):
        return None
    if mode == "A" and not (score >= 4 and touched and rejected and mss):
        return None
    if mode == "B":
        rev = "short" if bias == "long" else "long"
        if not (st.sweep(candles, rev) and st.choch(candles, rev)
                and displacement_at(candles, len(candles) - 1)):
            return None
        bias = rev
    return {"side": bias, "entry": bar["c"], "leg_high": leg["high"], "leg_low": leg["low"],
            "regime": regime_of(candles), "strategy": mode, "score": score}


def setup(candles: list[dict], mode: str, require_volume: bool = False) -> dict | None:
    if mode in ("A", "B"):
        return _ict_setup(candles, mode, require_volume)
    if mode == "C":
        s = breakout_setup(candles)
        return {**s, "strategy": "C"} if s else None
    if mode == "D":
        s = mean_reversion_setup(candles)
        return {**s, "strategy": "D"} if s else None
    raise ValueError("mode must be A, B, C, or D")


def make_position(s: dict, rr1: float, rr2: float) -> dict | None:
    entry = s["entry"]
    if "sl" in s:
        sl = s["sl"]
    else:
        dist = abs(entry - (s["leg_high"] if s["side"] == "short" else s["leg_low"]))
        if dist <= 0:
            return None
        sl = s["leg_high"] + 0.01 * dist if s["side"] == "short" else s["leg_low"] - 0.01 * dist
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    tp1 = entry - rr1 * risk if s["side"] == "short" else entry + rr1 * risk
    tp2 = entry - rr2 * risk if s["side"] == "short" else entry + rr2 * risk
    return {"side": s["side"], "entry": entry, "sl": sl, "tp1": tp1, "tp2": tp2,
            "regime": s["regime"], "strategy": s["strategy"],
            "score": s.get("score", 0), "partial_taken": False}


def run_backtest(candles: list[dict], mode: str, fee_r: float = 0.06, slip_r: float = 0.03,
                 partial: float = 0.5, rr1: float = 1.25, rr2: float = 2.5,
                 require_volume: bool = False) -> dict:
    if len(candles) < 60:
        raise ValueError("at least 60 candles are required")
    start = 230 if mode == "C" else 60
    trades, pos = [], None
    equity = peak = dd = 0.0
    for i in range(start, len(candles)):
        bar = candles[i]
        if pos:
            side = pos["side"]
            hit_sl = bar["h"] >= pos["sl"] if side == "short" else bar["l"] <= pos["sl"]
            hit_tp2 = bar["l"] <= pos["tp2"] if side == "short" else bar["h"] >= pos["tp2"]
            event, r = None, 0.0
            if not pos["partial_taken"]:
                hit_tp1 = bar["l"] <= pos["tp1"] if side == "short" else bar["h"] >= pos["tp1"]
                if hit_sl:
                    r, event = -1.0, "sl"
                elif hit_tp2:
                    r, event = rr2, "tp2"
                elif hit_tp1:
                    r, event = partial * rr1, "tp1"
                    pos["partial_taken"] = True
                    pos["sl"] = pos["entry"]
            else:
                if hit_sl:
                    r, event = partial * rr1, "be_after_tp1"
                elif hit_tp2:
                    r, event = partial * rr1 + (1 - partial) * rr2, "tp2_after_tp1"
            if event and event != "tp1":
                r -= fee_r + slip_r
                equity += r
                peak = max(peak, equity)
                dd = max(dd, peak - equity)
                trades.append({"time": bar["t"], "side": side, "strategy": pos["strategy"],
                               "r": round(r, 4), "event": event, "regime": pos["regime"],
                               "score": pos["score"]})
                pos = None
            elif event == "tp1":
                trades.append({"time": bar["t"], "side": side, "strategy": pos["strategy"],
                               "r": round(r, 4), "event": event, "regime": pos["regime"],
                               "score": pos["score"], "note": "partial; position continues at BE"})
            continue
        s = setup(candles[:i], mode, require_volume)
        if s:
            pos = make_position(s, rr1, rr2)
    closed = [t for t in trades if t["event"] != "tp1"]
    wins = sum(t["r"] > 0 for t in closed)
    losses = sum(t["r"] < 0 for t in closed)
    gw = sum(t["r"] for t in closed if t["r"] > 0)
    gl = -sum(t["r"] for t in closed if t["r"] < 0)
    net_r = round(sum(t["r"] for t in closed), 3)
    by_regime: dict = {}
    for t in closed:
        q = by_regime.setdefault(t["regime"], {"trades": 0, "net_r": 0.0})
        q["trades"] += 1
        q["net_r"] = round(q["net_r"] + t["r"], 3)
    pf = round(gw / gl, 3) if gl else None
    expectancy = round(net_r / len(closed), 4) if closed else 0
    return {
        "mode": mode, "trades": len(closed), "wins": wins, "losses": losses,
        "win_rate_pct": round(100 * wins / len(closed), 2) if closed else 0,
        "profit_factor": pf, "expectancy_r": expectancy, "net_r": net_r,
        "max_drawdown_r": round(dd, 3), "by_regime": by_regime,
        "accepted": bool(len(closed) >= 100 and pf and pf >= 1.20
                         and expectancy > 0 and net_r > 0),
        "acceptance_note": "needs >=100 trades, PF>=1.20, expectancy>0, net R>0 + OOS pass",
        "trades_detail": trades,
    }


def run_all(candles: list[dict], **kwargs) -> dict:
    return {m: run_backtest(candles, m, **kwargs) for m in "ABCD"}


def split_in_out(candles: list[dict], ratio: float = 0.7) -> tuple[list[dict], list[dict]]:
    cut = int(len(candles) * ratio)
    return candles[:cut], candles[cut:]
