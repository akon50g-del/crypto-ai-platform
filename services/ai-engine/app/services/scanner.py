"""Scan orchestrator: one cycle = all symbols x enabled strategies.

Every scan persists an Analysis (audit snapshot). Signals persist at
WATCH/READY/NO_SETUP(>=watch threshold for learning); only READY alerts.
"""
from __future__ import annotations

import logging

from app.core.config import CONFIG
from app.core.filters import correlation_guard
from app.indicators import structure as st
from app.indicators.poi import fvgs, order_blocks
from app.indicators.technicals import adx, atr, regime as regime_of
from app.models.db import get_session, init_db
from app.services import repository as repo
from app.services.market_data import CandleCache, fetch_live_price
from app.strategies.base import MarketContext
from app.strategies.strategy_a_continuation import StrategyA
from app.strategies.strategy_b_sweep_reversal import StrategyB
from app.strategies.strategy_c_breakout_retest import StrategyC
from app.strategies.strategy_d_mean_reversion import StrategyD

log = logging.getLogger("ai-engine.scanner")
STRATEGY_CLASSES = {"A": StrategyA, "B": StrategyB, "C": StrategyC, "D": StrategyD}


def build_snapshot(symbol: str, candles: dict[str, list[dict]], btc_4h: list[dict],
                   price_info: dict) -> dict:
    c4h, c1h = candles.get("4h", []), candles.get("1h", [])
    n = CONFIG["structure"]["swingN"]
    btc_bias = st.bias(btc_4h, n) if len(btc_4h) >= 25 else "range"
    return {
        "price": price_info["price"], "price_source": price_info["source"],
        "price_time_utc": price_info["time_utc"],
        "bias": st.bias(c4h, n) if len(c4h) >= 25 else "range",
        "regime": regime_of(c1h, n) if len(c1h) >= 25 else "unknown",
        "adx": adx(c1h) if c1h else None, "atr": atr(c1h) if c1h else None,
        "structure": {**st.liquidity_pools(c1h, n), "last_leg": st.last_leg(c1h, n),
                      "premium_discount": st.premium_discount(c1h, n),
                      "inducement": st.inducement(c1h, n)} if len(c1h) >= 25 else {},
        "poi": {"open_fvgs": [f for f in fvgs(c1h) if f["status"] != "filled"][-6:],
                "order_blocks": order_blocks(c1h)[-4:]} if len(c1h) >= 25 else {},
        "btc_context": {"btc_bias_4h": btc_bias,
                        "btc_pools": st.liquidity_pools(btc_4h, n) if len(btc_4h) >= 25 else {}},
        "enrichment": None,  # Nansen/liquidations: optional, off by default
    }


def analyze_symbol(symbol: str, cache: CandleCache | None = None,
                   btc_4h: list[dict] | None = None) -> dict:
    cache = cache or CandleCache()
    tfs = CONFIG["scan"]["timeframes"]
    candles = {tf: cache.get(symbol, tf, 300)
               for tf in {tfs["bias"], tfs["entryZone"], tfs["confirmation"]}}
    if btc_4h is None:
        btc_4h = candles["4h"] if symbol == "BTCUSDT" else cache.get("BTCUSDT", "4h", 300)
    price_info = fetch_live_price(symbol)
    snapshot = build_snapshot(symbol, candles, btc_4h, price_info)
    news_events: list[dict] = []
    has_active = False
    try:  # calendar + active-signal state must never break the scan
        with get_session() as session:
            news_events = repo.load_news_events(session)
            sym = repo.ensure_symbol(session, symbol)
            has_active = repo.has_active_signal(session, sym.id)
            session.commit()
    except Exception as exc:
        log.warning("news/active-signal lookup failed for %s: %s", symbol, exc)
    ctx = MarketContext(symbol=symbol, candles=candles, btc_candles_4h=btc_4h,
                        btc_bias=snapshot["btc_context"]["btc_bias_4h"],
                        news_events=news_events, has_active_signal=has_active)
    candidates = []
    for code, cls in STRATEGY_CLASSES.items():
        if not CONFIG["strategies"].get(code, {}).get("enabled", False):
            continue
        try:
            cand = cls(CONFIG).evaluate(ctx)
        except Exception as exc:  # one strategy must never kill the scan
            log.exception("strategy %s failed on %s: %s", code, symbol, exc)
            continue
        if cand is not None:
            candidates.append(cand)
    return {"snapshot": snapshot, "candidates": candidates, "candles": candles}


def run_scan(symbols: list[str] | None = None, persist: bool = True) -> dict:
    init_db()
    cache = CandleCache()
    symbols = symbols or CONFIG["scan"]["symbols"]
    session = get_session()
    run = repo.start_run(session) if persist else None
    errors: list[dict] = []
    created = 0
    results = []
    try:
        btc_4h = cache.get("BTCUSDT", "4h", 300)
        latest_15m: dict[str, list[dict]] = {}
        for symbol in symbols:
            try:
                out = analyze_symbol(symbol, cache, btc_4h)
                latest_15m[symbol] = out["candles"].get("15m", [])
                analysis_id = None
                if persist:
                    analysis = repo.save_analysis(session, symbol, out["snapshot"])
                    analysis_id = analysis.id
                    session.commit()
                saved = []
                for cand in out["candidates"]:
                    if persist:
                        s2 = get_session()
                        try:
                            sym_row = repo.ensure_symbol(s2, symbol)
                            if (CONFIG["filters"]["oneActiveSignalPerSymbol"]
                                    and cand.status == "READY"
                                    and repo.has_active_signal(s2, sym_row.id)):
                                cand.status = "WATCH"
                                cand.context["downgraded"] = "active signal exists"
                            if cand.status == "READY" and not correlation_guard(
                                    repo.active_sides(s2), cand.side,
                                    CONFIG["scan"]["maxCorrelatedSignals"]):
                                cand.status = "WATCH"
                                cand.context["downgraded"] = "correlation limit"
                            row = repo.save_signal(s2, cand, analysis_id)
                            s2.commit()
                            saved.append({"id": row.id, "strategy": cand.strategy,
                                          "side": cand.side, "status": cand.status,
                                          "score": cand.score})
                            created += 1
                        finally:
                            s2.close()
                    else:
                        saved.append({"strategy": cand.strategy, "side": cand.side,
                                      "status": cand.status, "score": cand.score})
                results.append({"symbol": symbol, "price": out["snapshot"]["price"],
                                "bias": out["snapshot"]["bias"],
                                "regime": out["snapshot"]["regime"], "signals": saved})
            except Exception as exc:
                log.exception("scan failed for %s", symbol)
                errors.append({"symbol": symbol, "error": str(exc)})
        outcome_updates = []
        if persist:
            s3 = get_session()
            try:
                outcome_updates = repo.track_outcomes(s3, latest_15m)
                s3.commit()
            finally:
                s3.close()
        if persist and run is not None:
            repo.finish_run(session, run, len(symbols), created, errors)
            session.commit()
        return {"symbols_scanned": len(symbols), "signals_created": created,
                "errors": errors, "results": results, "outcome_updates": outcome_updates}
    finally:
        session.close()
