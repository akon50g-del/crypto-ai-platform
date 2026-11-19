#!/usr/bin/env python3
"""رسم شارت شموع مع مناطق ICT ومستويات الصفقة والسعر الحي.

Usage:
  python chart_draw.py --csv candles.csv --out chart.png --title "XRP/USDT 1H"
  python chart_draw.py --json cdc_1h.json --drop-last --levels levels.json --out chart.png
  python chart_draw.py --csv candles.csv --levels levels.json --out chart.png --title "XRP/USDT 1H"

المدخل: --json (ملف محفوظ من get_candlestick، الترتيب لا يهم) أو --csv بأعمدة time,open,high,low,close (من الأقدم للأحدث، أو يُعكس تلقائيًا). --drop-last يتجاهل الشمعة الأحدث غير المكتملة.

levels.json (كل المفاتيح اختيارية):
{
  "live_price": 1.0408,
  "live_label": "Alpha Vantage 05:10 UTC",
  "zones": [
    {"label": "FVG 1H", "top": 1.0450, "bottom": 1.0420, "start": 38, "color": "#26a69a"},
    {"label": "OB 4H",  "top": 1.0520, "bottom": 1.0490, "start": 30, "color": "#f5b041"}
  ],
  "lines": [
    {"label": "Entry", "price": 1.0440, "color": "#4fc3f7"},
    {"label": "SL",    "price": 1.0560, "color": "#ef5350"},
    {"label": "TP1",   "price": 1.0300, "color": "#66bb6a"}
  ]
}
"start" رقم الشمعة (بدءًا من 0) التي تبدأ عندها المنطقة، وتمتد للحافة اليمنى.
الألوان الافتراضية: الشموع الصاعدة أخضر والهابطة أحمر.
"""
import argparse, json
from candles import load_candles
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BG = "#111418"
FG = "#e6e6e6"
UP = "#26a69a"
DOWN = "#ef5350"


def fmt_price(p):
    return f"{p:.4f}" if abs(p) < 10 else f"{p:,.2f}"


def short_time(t):
    """2026-11-10T04:00:00Z -> 11-10 04:00"""
    s = str(t)
    return s[5:16].replace("T", " ") if len(s) >= 16 else s[-8:]


def draw(candles, levels, title, out):
    n = len(candles)
    lo = min(c["l"] for c in candles)
    hi = max(c["h"] for c in candles)
    span = hi - lo or 1e-9

    # امتداد المحور الصادي ليتسع للمناطق والخطوط خارج نطاق الشموع
    prices = [lo, hi]
    for z in levels.get("zones", []):
        prices += [z["top"], z["bottom"]]
    for ln in levels.get("lines", []):
        prices.append(ln["price"])
    if "live_price" in levels:
        prices.append(levels["live_price"])
    ymin, ymax = min(prices), max(prices)
    pad = (ymax - ymin) * 0.04 or span * 0.04

    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=130)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#333842")
    ax.tick_params(colors=FG, labelsize=9)
    ax.grid(color="#222831", linewidth=0.6)

    # المناطق أولًا (خلف الشموع)
    for z in levels.get("zones", []):
        s = int(z.get("start", 0))
        color = z.get("color", "#f5b041")
        width = (n - 1 - s) + 1.6
        ax.add_patch(Rectangle((s - 0.5, z["bottom"]), width, z["top"] - z["bottom"],
                               facecolor=color, alpha=0.18, edgecolor=color,
                               linewidth=0.8, zorder=1))
        if z.get("label"):
            ax.text(s - 0.3, z["top"], f" {z['label']}", color=color, fontsize=8,
                    va="bottom", ha="left", zorder=5)

    # الشموع
    body_min = span * 0.002
    w = 0.6
    for i, c in enumerate(candles):
        color = UP if c["c"] >= c["o"] else DOWN
        ax.vlines(i, c["l"], c["h"], color=color, linewidth=1, zorder=2)
        b_lo, b_hi = min(c["o"], c["c"]), max(c["o"], c["c"])
        ax.add_patch(Rectangle((i - w / 2, b_lo), w, max(b_hi - b_lo, body_min),
                               color=color, zorder=3))

    # خطوط الصفقة
    for ln in levels.get("lines", []):
        color = ln.get("color", "#aaaaaa")
        ax.axhline(ln["price"], color=color, linestyle="--", linewidth=1, zorder=4)
        ax.text(n + 0.2, ln["price"], f" {ln.get('label', '')} {fmt_price(ln['price'])}",
                color=color, fontsize=8, va="center", ha="left", zorder=5,
                bbox=dict(boxstyle="square,pad=0.15", fc=BG, ec="none"))

    # السعر الحي
    if "live_price" in levels:
        p = levels["live_price"]
        ax.axhline(p, color="#ffffff", linestyle=":", linewidth=1.2, zorder=4)
        label = levels.get("live_label", "Live")
        ax.text(n + 0.2, p, f" {label} {fmt_price(p)}", color="#ffffff",
                fontsize=8, va="center", ha="left", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="#ffffff", lw=0.6))

    ax.set_xlim(-1, n + 9)
    ax.set_ylim(ymin - pad, ymax + pad)

    # محور زمني: حوالي 6 تسميات
    step = max(1, n // 6)
    idx = list(range(0, n, step))
    ax.set_xticks(idx)
    ax.set_xticklabels([short_time(candles[i]["t"]) for i in idx], rotation=0, fontsize=8)
    ax.set_title(title, color=FG, fontsize=12, loc="left", pad=10)
    ax.set_ylabel("Price (USD)", color=FG, fontsize=9)
    ax.yaxis.set_label_position("left")
    fig.tight_layout()
    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv")
    src.add_argument("--json")
    ap.add_argument("--drop-last", action="store_true", help="تجاهل الشمعة الأحدث غير المكتملة")
    ap.add_argument("--levels", help="ملف JSON للمناطق والخطوط والسعر الحي")
    ap.add_argument("--out", default="chart.png")
    ap.add_argument("--title", default="Chart")
    a = ap.parse_args()
    candles = load_candles(a.json, "json") if a.json else load_candles(a.csv, "csv")
    if a.drop_last:
        candles = candles[:-1]
    levels = json.load(open(a.levels)) if a.levels else {}
    draw(candles, levels, a.title, a.out)
