"""Path B — Liquidity Sweep Reversal. No sweep + no MSS = no setup. §5B."""
from __future__ import annotations

from app.core.filters import check_filters
from app.indicators import structure as st
from app.indicators.technicals import atr_anomalous, regime
from app.strategies.base import BaseStrategy, MarketContext, SignalCandidate
from app.strategies.common import build_candidate, mss_with_displacement


class StrategyB(BaseStrategy):
    code = "B"
    name = "Liquidity Sweep Reversal"

    def evaluate(self, ctx: MarketContext) -> SignalCandidate | None:
        c4h, c1h, c15 = ctx.tf("4h"), ctx.tf("1h"), ctx.tf("15m")
        if len(c1h) < 25 or len(c15) < 25:
            return None
        cfg = self.config
        n = cfg["structure"]["swingN"]
        htf_bias = st.bias(c4h, n) if len(c4h) >= 25 else "range"
        # Reversal side: sweep of lows -> long; sweep of highs -> short
        for side in ("long", "short"):
            swept = st.sweep(c1h, side, n) or st.sweep(c15, side, n)
            if not swept:
                continue
            mss = mss_with_displacement(c15, side, cfg)
            if not mss:
                continue  # hard rule: no MSS, no Path B
            leg = st.last_leg(c1h, n)
            origin = (leg["low"] if side == "long" else leg["high"]) if leg else c1h[-1]["c"]
            built = build_candidate(symbol=ctx.symbol, strategy="B", side=side,
                                    ctx_candles_1h=c1h, candles_15m=c15, htf_bias=htf_bias,
                                    swept=True, mss=True, cfg=cfg,
                                    regime_name=regime(c1h, n), origin=origin)
            scored = built["scored"]
            filt = check_filters(
                side=side, strategy="B", final_rr=built["final_rr"],
                min_final_rr=cfg["risk"]["minFinalRR"], htf_bias=htf_bias,
                btc_bias=ctx.btc_bias, btc_context_enabled=cfg["filters"]["btcContext"],
                atr_anomaly=atr_anomalous(c15) if cfg["filters"]["atrAnomalyGuard"] else False,
                has_active_signal=ctx.has_active_signal, news_events=ctx.news_events,
                news_blackout_minutes=cfg["filters"]["newsBlackoutMinutes"])
            status = scored["status"] if filt["passed"] else ("WATCH" if scored["score"] >= 5 else "NO_SETUP")
            return SignalCandidate(
                symbol=ctx.symbol, strategy="B", side=side,
                entry_zone_low=built["entry_zone_low"], entry_zone_high=built["entry_zone_high"],
                stop_loss=built["stop_loss"], tp1=built["tp1"], tp2=built["tp2"],
                invalidation=built["invalidation"], score=scored["score"],
                score_breakdown=scored["breakdown"], grade=scored["grade"], status=status,
                regime=built["regime"],
                reason_ar=f"مسار B انعكاس بعد سحب سيولة + MSS على 15m، Score {scored['score']}/10",
                reason_en=f"Path B sweep reversal + 15m MSS, score {scored['score']}/10",
                context={"filters": filt, "poi": built["poi"], "pools": built["pools"],
                         "final_rr": built["final_rr"], "swept": True, "mss": True})
        return None
