#!/usr/bin/env python3
"""Position sizing for small accounts.
Usage:
  python position_size.py --balance 100 --risk 1 --entry 1.14 --sl 1.159 --tp 1.09,1.0763,1.05 --leverage 3
qty = (balance * risk%) / |entry - sl| ; notional = qty * entry ; margin = notional / leverage.
Works for long and short (direction inferred from entry vs sl). Fees/slippage NOT included:
check the exchange's current fee schedule and minimum order size yourself.
"""
import argparse, json

ap = argparse.ArgumentParser()
ap.add_argument("--balance", type=float, required=True)
ap.add_argument("--risk", type=float, default=1.0, help="percent of balance risked (default 1)")
ap.add_argument("--entry", type=float, required=True)
ap.add_argument("--sl", type=float, required=True)
ap.add_argument("--tp", default="", help="comma separated targets")
ap.add_argument("--leverage", type=float, default=3.0)
a = ap.parse_args()

dist = abs(a.entry - a.sl)
if dist == 0:
    raise SystemExit("entry and sl must differ")
side = "short" if a.sl > a.entry else "long"
risk_amt = a.balance * a.risk / 100
qty = risk_amt / dist
notional = qty * a.entry
out = dict(side=side, risk_amount=round(risk_amt, 4), sl_distance=round(dist, 6),
           sl_distance_pct=round(dist / a.entry * 100, 3), qty=round(qty, 2),
           notional=round(notional, 2), margin_at_leverage=round(notional / a.leverage, 2),
           leverage=a.leverage, notional_vs_balance=round(notional / a.balance, 2), targets=[])
for t in filter(None, a.tp.split(",")):
    t = float(t)
    reward = (a.entry - t) if side == "short" else (t - a.entry)
    out["targets"].append(dict(price=t, pnl=round(reward * qty, 2), rr=round(reward / dist, 2)))
if risk_amt / a.balance > 0.02:
    out["warning"] = "risk above 2% of balance"
print(json.dumps(out, indent=2))
