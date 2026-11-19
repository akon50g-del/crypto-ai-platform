#!/usr/bin/env python3
"""ICT structure scanner.
Usage:
  python ict_analyze.py --json cdc_4h.json                    # saved output of Crypto.com get_candlestick tool (preferred)
  python ict_analyze.py --csv candles.csv                     # csv columns: time,open,high,low,close
  python ict_analyze.py --pair XRPUSD --interval 60           # Kraken (usually blocked: needs api.kraken.com allowed)
Options: --drop-last  (ignore the still-forming newest candle)
Intervals for Kraken (minutes): 5 15 60 240 1440. Prints JSON.
All zones are computed from real OHLC; wicks included.
"""
import argparse, json, sys, urllib.request
from candles import load_candles

def fetch_kraken(pair, interval):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    if data.get("error"):
        sys.exit(f"Kraken error: {data['error']}")
    res = data["result"]
    key = next(k for k in res if k != "last")
    rows = res[key][:-1]  # drop the still-forming candle
    return [dict(t=int(x[0]), o=float(x[1]), h=float(x[2]), l=float(x[3]), c=float(x[4])) for x in rows]

def swings(c, n=2):
    hi, lo = [], []
    for i in range(n, len(c) - n):
        if all(c[i]["h"] > c[i-k]["h"] and c[i]["h"] > c[i+k]["h"] for k in range(1, n+1)):
            hi.append((i, c[i]["h"]))
        if all(c[i]["l"] < c[i-k]["l"] and c[i]["l"] < c[i+k]["l"] for k in range(1, n+1)):
            lo.append((i, c[i]["l"]))
    return hi, lo

def fvgs(c):
    out = []
    for i in range(2, len(c)):
        if c[i]["l"] > c[i-2]["h"]:
            lo_, hi_, kind = c[i-2]["h"], c[i]["l"], "bullish"
        elif c[i]["h"] < c[i-2]["l"]:
            lo_, hi_, kind = c[i]["h"], c[i-2]["l"], "bearish"
        else:
            continue
        later = c[i+1:]
        if kind == "bullish":
            filled = any(x["l"] <= lo_ for x in later)
            touched = any(x["l"] < hi_ for x in later)
        else:
            filled = any(x["h"] >= hi_ for x in later)
            touched = any(x["h"] > lo_ for x in later)
        out.append(dict(kind=kind, low=lo_, high=hi_, index=i,
                        status="filled" if filled else ("partial" if touched else "unfilled")))
    return out

def order_blocks(c, mult=1.5, lookback=20):
    out = []
    for i in range(lookback, len(c)):
        avg = sum(abs(x["c"] - x["o"]) for x in c[i-lookback:i]) / lookback
        body = c[i]["c"] - c[i]["o"]
        if abs(body) < mult * avg:
            continue
        want_bull_candle = body < 0  # bearish displacement -> last bullish candle is the OB
        for j in range(i - 1, max(i - 6, 0), -1):
            if (c[j]["c"] > c[j]["o"]) == want_bull_candle:
                out.append(dict(kind="bearish" if body < 0 else "bullish", low=min(c[j]["o"], c[j]["c"]),
                                high=max(c[j]["o"], c[j]["c"]), wick_low=c[j]["l"], wick_high=c[j]["h"],
                                index=j, displacement_index=i))
                break
    return out

def equal_levels(pts, tol=0.0015):
    eq = []
    for a in range(len(pts)):
        for b in range(a + 1, len(pts)):
            if abs(pts[a][1] - pts[b][1]) / pts[a][1] <= tol:
                eq.append(round((pts[a][1] + pts[b][1]) / 2, 8))
    return sorted(set(eq))

def analyze(c):
    price = c[-1]["c"]
    sh, sl = swings(c)
    bias = "range"
    if len(sh) >= 2 and len(sl) >= 2:
        if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]: bias = "bearish (LH+LL)"
        elif sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]: bias = "bullish (HH+HL)"
    leg = None
    if sh and sl:
        (ih, ph), (il, pl) = sh[-1], sl[-1]
        rng = ph - pl
        if il > ih:   # last leg down -> retrace up = premium, look to sell
            leg = dict(direction="down", high=ph, low=pl, ote_low=pl + .62*rng, ote_high=pl + .79*rng, eq=pl + .5*rng)
        else:         # last leg up -> retrace down = discount, look to buy
            leg = dict(direction="up", high=ph, low=pl, ote_low=ph - .79*rng, ote_high=ph - .62*rng, eq=ph - .5*rng)
    f = [x for x in fvgs(c) if x["status"] != "filled"][-6:]
    ob = order_blocks(c)[-4:]
    bsl = sorted(p for _, p in sh if p > price)[:4]
    ssl = sorted((p for _, p in sl if p < price), reverse=True)[:4]
    return dict(price=price, candles=len(c), bias=bias, last_leg=leg,
                open_fvgs=f, order_blocks=ob,
                bsl_above=bsl, ssl_below=ssl,
                equal_highs=equal_levels(sh), equal_lows=equal_levels(sl),
                last_swing_highs=[p for _, p in sh[-3:]], last_swing_lows=[p for _, p in sl[-3:]])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="ملف JSON محفوظ من أداة get_candlestick (الترتيب لا يهم)")
    ap.add_argument("--csv", help="ملف CSV بأعمدة time,open,high,low,close")
    ap.add_argument("--pair", help="Kraken، يعمل فقط إن كان api.kraken.com مسموحًا")
    ap.add_argument("--interval", type=int, default=60, help="دقائق لـ Kraken: 5 15 60 240 1440")
    ap.add_argument("--drop-last", action="store_true", help="تجاهل الشمعة الأحدث لأنها ما زالت تتشكل")
    a = ap.parse_args()
    if a.json:
        candles = load_candles(a.json, "json")
    elif a.csv:
        candles = load_candles(a.csv, "csv")
    elif a.pair:
        candles = fetch_kraken(a.pair, a.interval)  # يتجاهل الشمعة الجارية تلقائيًا
    else:
        ap.error("أعطِ --json أو --csv")
    if a.drop_last and not a.pair:
        candles = candles[:-1]
    if len(candles) < 25:
        sys.exit(f"شموع قليلة جدًا ({len(candles)}): التحليل يحتاج 25 شمعة على الأقل")
    print(json.dumps(analyze(candles), indent=2))
