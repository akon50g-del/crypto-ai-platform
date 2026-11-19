#!/usr/bin/env python3
"""Conservative walk-forward backtester for four crypto strategies.

CSV columns: time,open,high,low,close[,volume] (oldest first).
Modes:
  A = ICT continuation
  B = liquidity-sweep reversal
  C = trend pullback / breakout retest
  D = mean reversion in a range
  all = run A-D independently

Signals use only candles before the decision candle. Results are in R after
configurable fee/slippage charges expressed in R. This is a research tool,
not an execution engine.
"""
import argparse, csv, json, statistics


def load_csv(path):
    """يقرأ الشموع ويرتّبها من الأقدم للأحدث حسب عمود time (يدعم ms وISO).
    إن غاب الوقت أو تعذّر تحليله يُفترض أن الملف مرتّب من الأقدم للأحدث."""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from candles import _sort_key
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    keys = [_sort_key(r.get("time")) if r.get("time") not in (None, "") else None for r in rows]
    if rows and all(k is not None for k in keys):
        rows = [r for _, r in sorted(zip(keys, rows), key=lambda x: x[0])]
        # شمعتان بنفس الوقت = بيانات مكررة تُفسد النتائج
        ts = sorted(keys)
        if any(a == b for a, b in zip(ts, ts[1:])):
            raise SystemExit("الملف يحتوي شموعًا مكررة بنفس الوقت، نظّفه أولًا")
    return [{"time": r["time"], "o": float(r["open"]), "h": float(r["high"]),
             "l": float(r["low"]), "c": float(r["close"]),
             "v": float(r.get("volume", 0) or 0)} for r in rows]


def sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else None


def ema(values, n):
    if len(values) < n:
        return None
    value = sum(values[:n]) / n
    alpha = 2 / (n + 1)
    for x in values[n:]:
        value = alpha * x + (1 - alpha) * value
    return value


def atr(c, n=14):
    if len(c) < n + 1:
        return None
    trs = []
    for i in range(1, len(c)):
        trs.append(max(c[i]["h"] - c[i]["l"], abs(c[i]["h"] - c[i-1]["c"]),
                      abs(c[i]["l"] - c[i-1]["c"])))
    return sum(trs[-n:]) / n


def adx(c, n=14):
    if len(c) < 2 * n + 1:
        return None
    trs, plus, minus = [], [], []
    for i in range(1, len(c)):
        up = c[i]["h"] - c[i-1]["h"]
        down = c[i-1]["l"] - c[i]["l"]
        trs.append(max(c[i]["h"] - c[i]["l"], abs(c[i]["h"] - c[i-1]["c"]), abs(c[i]["l"] - c[i-1]["c"])))
        plus.append(up if up > down and up > 0 else 0.0)
        minus.append(down if down > up and down > 0 else 0.0)
    dx = []
    for i in range(n - 1, len(trs)):
        tr = sum(trs[i-n+1:i+1])
        if tr <= 0:
            continue
        pdi = 100 * sum(plus[i-n+1:i+1]) / tr
        mdi = 100 * sum(minus[i-n+1:i+1]) / tr
        dx.append(100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi else 0)
    return sum(dx[-n:]) / n if len(dx) >= n else None


def swings(c, n=2):
    hi, lo = [], []
    for i in range(n, len(c) - n):
        if all(c[i]["h"] > c[i-k]["h"] and c[i]["h"] > c[i+k]["h"] for k in range(1, n+1)):
            hi.append((i, c[i]["h"]))
        if all(c[i]["l"] < c[i-k]["l"] and c[i]["l"] < c[i+k]["l"] for k in range(1, n+1)):
            lo.append((i, c[i]["l"]))
    return hi, lo


def regime(c):
    sh, sl = swings(c)
    if len(sh) >= 2 and len(sl) >= 2:
        if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
            return "bull_trend"
        if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
            return "bear_trend"
    ranges = [x["h"] - x["l"] for x in c[-20:]]
    if not ranges:
        return "unknown"
    med = statistics.median(ranges)
    return "high_vol_range" if ranges[-1] > 1.5 * med else "range"


def displacement(c, i, mult=1.5):
    if i < 20:
        return False
    avg = sum(abs(x["c"] - x["o"]) for x in c[i-20:i]) / 20
    body = abs(c[i]["c"] - c[i]["o"])
    vols = [x["v"] for x in c[i-20:i] if x["v"] > 0]
    vol_ok = not (c[i]["v"] > 0 and vols) or c[i]["v"] >= statistics.mean(vols)
    return avg > 0 and body >= mult * avg and vol_ok


def fvg_and_ob(c, direction):
    fvg = ob = False
    for i in range(2, len(c)):
        if c[i]["l"] > c[i-2]["h"]:
            lo, hi, kind = c[i-2]["h"], c[i]["l"], "long"
        elif c[i]["h"] < c[i-2]["l"]:
            lo, hi, kind = c[i]["h"], c[i-2]["l"], "short"
        else:
            continue
        unfilled = not any((x["l"] <= lo if kind == "long" else x["h"] >= hi) for x in c[i+1:])
        if kind == direction and unfilled and c[-1]["l"] <= hi and c[-1]["h"] >= lo:
            fvg = True
    for i in range(20, len(c)):
        if not displacement(c, i):
            continue
        j = i - 1
        if direction == "short" and c[i]["c"] < c[i]["o"] and c[j]["c"] > c[j]["o"]:
            ob |= c[j]["o"] <= c[-1]["c"] <= c[j]["c"]
        if direction == "long" and c[i]["c"] > c[i]["o"] and c[j]["c"] < c[j]["o"]:
            ob |= c[j]["c"] <= c[-1]["c"] <= c[j]["o"]
    return fvg, ob


def confirmation(c, direction):
    sh, sl = swings(c)
    last = c[-1]
    mss = sweep = False
    if direction == "long" and sh and last["c"] > sh[-1][1] and displacement(c, len(c)-1):
        mss = True
    if direction == "short" and sl and last["c"] < sl[-1][1] and displacement(c, len(c)-1):
        mss = True
    if direction == "long" and sl:
        prior = [p for i, p in sl if i < len(c)-1]
        sweep = bool(prior and last["l"] < min(prior) and last["c"] > min(prior))
    if direction == "short" and sh:
        prior = [p for i, p in sh if i < len(c)-1]
        sweep = bool(prior and last["h"] > max(prior) and last["c"] < max(prior))
    return mss, sweep


def ict_setup(c, mode, require_volume=False):
    sh, sl = swings(c)
    if len(sh) < 2 or len(sl) < 2:
        return None
    if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
        bias = "long"
    elif sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
        bias = "short"
    else:
        return None
    ih, ph = sh[-1]; il, pl = sl[-1]
    high, low = ph, pl
    ote = (pl + .62*(ph-pl), pl + .79*(ph-pl)) if il > ih else (ph-.79*(ph-pl), ph-.62*(ph-pl))
    lo, hi = min(ote), max(ote); bar = c[-1]
    touched = bar["l"] <= hi and bar["h"] >= lo
    rejected = (bias == "short" and bar["c"] < lo) or (bias == "long" and bar["c"] > hi)
    fvg, ob = fvg_and_ob(c, bias); mss, sweep = confirmation(c, bias)
    score = 1 + int(fvg or ob) + int(touched) + int(mss) + int(sweep)
    if require_volume and not displacement(c, len(c)-1):
        return None
    if mode == "A" and not (score >= 4 and touched and rejected and mss):
        return None
    if mode == "B":
        rev = "short" if bias == "long" else "long"
        rmss, rsweep = confirmation(c, rev)
        if not (rsweep and rmss):
            return None
        bias = rev
    return {"side": bias, "entry": bar["c"], "leg_high": high, "leg_low": low,
            "regime": regime(c), "strategy": mode, "score": score}


def volume_ok(c, i, n=20):
    vals = [x["v"] for x in c[i-n:i] if x["v"] > 0]
    return not vals or c[i]["v"] >= statistics.mean(vals)


def breakout_setup(c):
    """C: trend filter + previous-bar Donchian break + current-bar retest."""
    if len(c) < 230:
        return None
    closes = [x["c"] for x in c]
    e50, e200, ad = ema(closes, 50), ema(closes, 200), adx(c)
    a = atr(c)
    if e50 is None or e200 is None or ad is None or a is None or ad <= 20:
        return None
    breakout, retest = c[-2], c[-1]
    level_hi = max(x["h"] for x in c[-22:-2]); level_lo = min(x["l"] for x in c[-22:-2])
    if e50 > e200 and breakout["c"] > level_hi and volume_ok(c, len(c)-2) and retest["l"] <= level_hi * 1.001 and retest["c"] > level_hi:
        sl = min(retest["l"], level_hi - .25*a) - .05*a
        return {"side":"long", "entry":retest["c"], "sl":sl, "regime":"bull_trend", "strategy":"C", "score":7}
    if e50 < e200 and breakout["c"] < level_lo and volume_ok(c, len(c)-2) and retest["h"] >= level_lo * .999 and retest["c"] < level_lo:
        sl = max(retest["h"], level_lo + .25*a) + .05*a
        return {"side":"short", "entry":retest["c"], "sl":sl, "regime":"bear_trend", "strategy":"C", "score":7}
    return None


def mean_reversion_setup(c):
    """D: low-ADX range sweep back inside the prior range."""
    if len(c) < 60:
        return None
    closes = [x["c"] for x in c]
    ad, a = adx(c), atr(c)
    mid = sma(closes, 20)
    if ad is None or a is None or mid is None or ad >= 20:
        return None
    prior = c[-25:-1]
    rh, rl = max(x["h"] for x in prior), min(x["l"] for x in prior)
    width = rh - rl
    if width <= 0 or width < 2*a:
        return None
    bar = c[-1]
    if bar["l"] < rl and bar["c"] > rl and bar["c"] < mid:
        return {"side":"long", "entry":bar["c"], "sl":bar["l"]-.15*a,
                "tp_level":mid, "regime":"range", "strategy":"D", "score":7}
    if bar["h"] > rh and bar["c"] < rh and bar["c"] > mid:
        return {"side":"short", "entry":bar["c"], "sl":bar["h"]+.15*a,
                "tp_level":mid, "regime":"range", "strategy":"D", "score":7}
    return None


def setup(c, mode, require_volume=False):
    if mode in ("A", "B"):
        return ict_setup(c, mode, require_volume)
    if mode == "C":
        return breakout_setup(c)
    if mode == "D":
        return mean_reversion_setup(c)
    raise ValueError("mode must be A, B, C, or D")


def make_position(s, rr1, rr2):
    entry = s["entry"]
    if "sl" in s:
        sl = s["sl"]
    else:
        dist = abs(entry - (s["leg_high"] if s["side"] == "short" else s["leg_low"]))
        if dist <= 0:
            return None
        sl = s["leg_high"] + .01*dist if s["side"] == "short" else s["leg_low"] - .01*dist
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    tp1 = entry - rr1*risk if s["side"] == "short" else entry + rr1*risk
    tp2 = entry - rr2*risk if s["side"] == "short" else entry + rr2*risk
    return {"side":s["side"], "entry":entry, "sl":sl, "tp1":tp1, "tp2":tp2,
            "regime":s["regime"], "strategy":s["strategy"], "score":s.get("score", 0),
            "partial_taken":False}


def run(c, mode, fee_r=.06, slip_r=.03, partial=.5, rr1=1.25, rr2=2.5, require_volume=False):
    if len(c) < 60:
        raise ValueError("at least 60 candles are required")
    start = 230 if mode == "C" else 60
    trades, pos = [], None
    equity = peak = dd = 0.0
    for i in range(start, len(c)):
        bar = c[i]
        if pos:
            side = pos["side"]
            hit_sl = bar["h"] >= pos["sl"] if side == "short" else bar["l"] <= pos["sl"]
            hit_tp2 = bar["l"] <= pos["tp2"] if side == "short" else bar["h"] >= pos["tp2"]
            event = None; r = 0.0
            if not pos["partial_taken"]:
                hit_tp1 = bar["l"] <= pos["tp1"] if side == "short" else bar["h"] >= pos["tp1"]
                if hit_sl:
                    r, event = -1.0, "sl"
                elif hit_tp2:
                    r, event = rr2, "tp2"
                elif hit_tp1:
                    r, event = partial*rr1, "tp1"
                    pos["partial_taken"] = True; pos["sl"] = pos["entry"]
            else:
                if hit_sl:
                    r, event = partial*rr1, "be_after_tp1"
                elif hit_tp2:
                    r, event = partial*rr1+(1-partial)*rr2, "tp2_after_tp1"
            if event:
                r -= fee_r + slip_r
                equity += r; peak = max(peak, equity); dd = max(dd, peak-equity)
                trades.append({"time":bar["time"], "side":side, "strategy":pos["strategy"],
                               "r":round(r,4), "event":event, "regime":pos["regime"],
                               "score":pos["score"]})
                pos = None
            continue
        s = setup(c[:i], mode, require_volume)
        if s:
            pos = make_position(s, rr1, rr2)
    wins = sum(t["r"] > 0 for t in trades); losses = sum(t["r"] < 0 for t in trades)
    gw = sum(t["r"] for t in trades if t["r"] > 0); gl = -sum(t["r"] for t in trades if t["r"] < 0)
    byreg = {}
    for t in trades:
        q = byreg.setdefault(t["regime"], {"trades":0, "net_r":0.0})
        q["trades"] += 1; q["net_r"] += t["r"]
    return {"mode":mode, "trades":len(trades), "wins":wins, "losses":losses,
            "win_rate_pct":round(100*wins/len(trades),2) if trades else 0,
            "profit_factor":round(gw/gl,3) if gl else None, "net_r":round(sum(t["r"] for t in trades),3),
            "max_drawdown_r":round(dd,3), "by_regime":byreg, "trades_detail":trades}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--mode", choices=["A", "B", "C", "D", "all", "strict", "balanced"], default="A")
    ap.add_argument("--fee-r", type=float, default=.06)
    ap.add_argument("--slip-r", type=float, default=.03)
    ap.add_argument("--require-volume", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    mode = "A" if a.mode == "strict" else ("B" if a.mode == "balanced" else a.mode)
    candles = load_csv(a.csv)
    if mode == "all":
        result = {m: run(candles, m, a.fee_r, a.slip_r, require_volume=a.require_volume) for m in "ABCD"}
        if not a.json:
            result = {m: {k:v for k,v in r.items() if k != "trades_detail"} for m,r in result.items()}
    else:
        result = run(candles, mode, a.fee_r, a.slip_r, require_volume=a.require_volume)
        if not a.json:
            result = {k:v for k,v in result.items() if k != "trades_detail"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
