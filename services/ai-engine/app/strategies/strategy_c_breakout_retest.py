"""Path C — Trend Pullback / Breakout Retest (EMA50/200 + ADX + Donchian).
Ported from breakout_setup() in backtest_ict.py. §5C."""
from __future__ import annotations

from app.core.filters import check_filters
from app.core.risk import rr
from app.indicators.technicals import adx, atr, ema, volume_ok
from app.strategies.base import BaseStrategy, MarketContext, SignalCandidate


def breakout_setup(candles: list[dict], adx_min: float = 20) -> dict | None:
    """Single-timeframe core (also used by the backtester)."""
    if len(candles) < 230:
        return None
    closes = [x["c"] for x in candles]
    e50, e200, ad, a = ema(closes, 50), ema(closes, 200), adx(candles), atr(candles)
    if e50 is None or e200 is None or ad is None or a is None or ad <= adx_min:
        return None
    breakout, retest = candles[-2], candles[-1]
    level_hi = max(x["h"] for x in candles[-22:-2])
    level_lo = min(x["l"] for x in candles[-22:-2])
    if (e50 > e200 and breakout["c"] > level_hi and volume_ok(candles, len(candles) - 2)
            and retest["l"] <= level_hi * 1.001 and retest["c"] > level_hi):
        sl = min(retest["l"], level_hi - 0.25 * a) - 0.05 * a
        return {"side": "long", "entry": retest["c"], "sl": sl, "regime": "bull_trend", "score": 7}
    if (e50 < e200 and breakout["c"] < level_lo and volume_ok(candles, len(candles) - 2)
            and retest["h"] >= level_lo * 0.999 and retest["c"] < level_lo):
        sl = max(retest["h"], level_lo + 0.25 * a) + 0.05 * a
        return {"side": "short", "entry": retest["c"], "sl": sl, "regime": "bear_trend", "score": 7}
    return None


class StrategyC(BaseStrategy):
    code = "C"
    name = "Trend Pullback / Breakout Retest"

    def evaluate(self, ctx: MarketContext) -> SignalCandidate | None:
        c1h = ctx.tf("1h")
        cfg = self.config
        setup = breakout_setup(c1h, cfg["strategies"]["C"].get("adxMin", 20))
        if not setup:
            return None
        side, entry, sl = setup["side"], setup["entry"], setup["sl"]
        risk = abs(entry - sl)
        tp1 = entry + 1.5 * risk if side == "long" else entry - 1.5 * risk
        tp2 = entry + cfg["risk"]["tp2R"] * risk if side == "long" else entry - cfg["risk"]["tp2R"] * risk
        final_rr = rr(entry, sl, tp2)
        filt = check_filters(
            side=side, strategy="C", final_rr=final_rr,
            min_final_rr=cfg["risk"]["minFinalRR"],
            htf_bias="bullish" if side == "long" else "bearish",
            btc_bias=ctx.btc_bias, btc_context_enabled=cfg["filters"]["btcContext"],
            atr_anomaly=False, has_active_signal=ctx.has_active_signal,
            news_events=ctx.news_events,
            news_blackout_minutes=cfg["filters"]["newsBlackoutMinutes"])
        return SignalCandidate(
            symbol=ctx.symbol, strategy="C", side=side,
            entry_zone_low=min(entry, sl) if side == "short" else sl,
            entry_zone_high=entry, stop_loss=sl, tp1=tp1, tp2=tp2,
            invalidation=sl, score=setup["score"],
            score_breakdown={"bias": 2, "poi": 0, "sweep": 0, "mss": 2,
                             "ltfConfirmation": 1, "liquidityTarget": 1, "rr": 1},
            grade="A", status="READY" if filt["passed"] else "WATCH",
            regime=setup["regime"],
            reason_ar="مسار C كسر وإعادة اختبار مع اتجاه EMA/ADX، Score 7/10",
            reason_en="Path C breakout retest with EMA/ADX trend, score 7/10",
            context={"filters": filt, "final_rr": final_rr})
