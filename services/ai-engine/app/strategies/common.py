"""Shared building blocks for strategies A/B (multi-timeframe ICT flow)."""
from __future__ import annotations

from app.core.risk import rr, stop_loss, targets_from_liquidity, weighted_rr
from app.core.scoring import compute_score
from app.indicators import structure as st
from app.indicators.poi import displacement_at, poi_snapshot
from app.indicators.technicals import atr


def mss_with_displacement(candles_15m: list[dict], side: str, cfg: dict) -> bool:
    """MSS/CHoCH on 15m: close breaks swing in trade direction + displacement."""
    if len(candles_15m) < 25:
        return False
    n = cfg["structure"]["swingN"]
    shifted = st.choch(candles_15m, side, n) or st.bos(candles_15m, side, n)
    disp = displacement_at(candles_15m, len(candles_15m) - 1,
                           cfg["structure"]["displacementMultiplier"],
                           cfg["structure"]["displacementLookback"])
    return bool(shifted and disp)


def rejection_candle(candles: list[dict], side: str, zone_low: float, zone_high: float) -> bool:
    """Closed rejection candle inside/out of the zone in bias direction (LTF confirm)."""
    if not candles:
        return False
    last = candles[-1]
    touched = last["l"] <= zone_high and last["h"] >= zone_low
    if not touched:
        return False
    return last["c"] > zone_high if side == "long" else last["c"] < zone_low


def build_candidate(*, symbol: str, strategy: str, side: str, ctx_candles_1h: list[dict],
                    candles_15m: list[dict], htf_bias: str, swept: bool, mss: bool,
                    cfg: dict, regime_name: str, origin: float) -> dict:
    """Assemble entry zone / SL / TPs / score for ICT paths A & B."""
    price = ctx_candles_1h[-1]["c"] if ctx_candles_1h else candles_15m[-1]["c"]
    poi = poi_snapshot(ctx_candles_1h, side)
    zone = poi["fvg"] or poi["ob"]
    if zone:
        zlow, zhigh = zone["low"], zone["high"]
    else:
        leg = st.last_leg(ctx_candles_1h, cfg["structure"]["swingN"])
        zlow, zhigh = (leg["ote_low"], leg["ote_high"]) if leg else (price, price)
    entry = (zlow + zhigh) / 2
    a = atr(ctx_candles_1h)
    sl = stop_loss(side, origin, a, tuple(cfg["risk"]["slAtrBuffer"]))
    pools = st.liquidity_pools(ctx_candles_1h, cfg["structure"]["swingN"])
    tp1, tp2, structural = targets_from_liquidity(
        side, entry, sl, pools["bsl_above"], pools["ssl_below"], cfg["risk"]["tp2R"])
    final_rr = max(rr(entry, sl, tp2), weighted_rr(entry, sl, tp1, tp2))
    ltf = rejection_candle(candles_15m, side, zlow, zhigh)
    scored = compute_score(
        bias_clear=htf_bias in ("bullish", "bearish"), poi_valid=poi["has_poi"],
        swept=swept, mss=mss, ltf_confirmed=ltf, liquidity_target=structural,
        rr_ok=final_rr >= cfg["risk"]["minFinalRR"], weights=cfg["scoring"]["weights"])
    return {
        "entry_zone_low": zlow, "entry_zone_high": zhigh, "entry": entry,
        "stop_loss": sl, "tp1": tp1, "tp2": tp2, "final_rr": final_rr,
        "rr_tp1": rr(entry, sl, tp1), "rr_tp2": rr(entry, sl, tp2),
        "poi": poi, "pools": pools, "scored": scored, "regime": regime_name,
        "invalidation": origin,
    }
