"""Path D — Mean Reversion in a range only (low ADX). Ported from
mean_reversion_setup() in backtest_ict.py. §5D."""
from __future__ import annotations

from app.core.filters import check_filters
from app.core.risk import rr
from app.indicators.technicals import adx, atr, sma
from app.strategies.base import BaseStrategy, MarketContext, SignalCandidate


def mean_reversion_setup(candles: list[dict], adx_max: float = 20) -> dict | None:
    if len(candles) < 60:
        return None
    closes = [x["c"] for x in candles]
    ad, a, mid = adx(candles), atr(candles), sma(closes, 20)
    if ad is None or a is None or mid is None or ad >= adx_max:
        return None
    prior = candles[-25:-1]
    rh, rl = max(x["h"] for x in prior), min(x["l"] for x in prior)
    width = rh - rl
    if width <= 0 or width < 2 * a:
        return None
    bar = candles[-1]
    if bar["l"] < rl and bar["c"] > rl and bar["c"] < mid:
        return {"side": "long", "entry": bar["c"], "sl": bar["l"] - 0.15 * a,
                "tp_level": mid, "tp2_level": rh, "regime": "range", "score": 7}
    if bar["h"] > rh and bar["c"] < rh and bar["c"] > mid:
        return {"side": "short", "entry": bar["c"], "sl": bar["h"] + 0.15 * a,
                "tp_level": mid, "tp2_level": rl, "regime": "range", "score": 7}
    return None


class StrategyD(BaseStrategy):
    code = "D"
    name = "Mean Reversion (Range)"

    def evaluate(self, ctx: MarketContext) -> SignalCandidate | None:
        c1h = ctx.tf("1h")
        cfg = self.config
        setup = mean_reversion_setup(c1h, cfg["strategies"]["D"].get("adxMax", 20))
        if not setup:
            return None
        side, entry, sl = setup["side"], setup["entry"], setup["sl"]
        tp1, tp2 = setup["tp_level"], setup["tp2_level"]
        final_rr = rr(entry, sl, tp2)
        filt = check_filters(
            side=side, strategy="D", final_rr=final_rr,
            min_final_rr=cfg["risk"]["minFinalRR"], htf_bias="range",
            btc_bias=ctx.btc_bias, btc_context_enabled=cfg["filters"]["btcContext"],
            atr_anomaly=False, has_active_signal=ctx.has_active_signal,
            news_events=ctx.news_events,
            news_blackout_minutes=cfg["filters"]["newsBlackoutMinutes"])
        return SignalCandidate(
            symbol=ctx.symbol, strategy="D", side=side,
            entry_zone_low=sl if side == "long" else entry,
            entry_zone_high=entry if side == "long" else sl,
            stop_loss=sl, tp1=tp1, tp2=tp2, invalidation=sl, score=setup["score"],
            score_breakdown={"bias": 0, "poi": 2, "sweep": 1, "mss": 2,
                             "ltfConfirmation": 1, "liquidityTarget": 1, "rr": 0},
            grade="A" if final_rr >= cfg["risk"]["minFinalRR"] else "WATCH",
            status="READY" if filt["passed"] else "WATCH",
            regime="range",
            reason_ar="مسار D ارتداد من حد النطاق بعد سحب، Score 7/10",
            reason_en="Path D range-edge sweep reversion, score 7/10",
            context={"filters": filt, "final_rr": final_rr})
