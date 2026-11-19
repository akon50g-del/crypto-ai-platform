"""Persistence helpers: save analyses/signals, dedupe active signals,
track outcomes (TP1 partial -> break-even -> TP2 / SL / invalidated / expired)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.db import (Analysis, EconomicEvent, EngineRun, Signal,
                           SignalOutcome, Symbol, get_session)

REGIME_MAP = {"bull_trend": "BULL_TREND", "bear_trend": "BEAR_TREND",
              "range": "RANGE", "high_vol_range": "HIGH_VOL_RANGE"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_symbol(session, symbol: str) -> Symbol:
    row = session.query(Symbol).filter_by(symbol=symbol).first()
    if row is None:
        row = Symbol(symbol=symbol, baseAsset=symbol.replace("USDT", ""))
        session.add(row)
        session.flush()
    return row


def has_active_signal(session, symbol_id: str) -> bool:
    return session.query(Signal).filter(
        Signal.symbolId == symbol_id,
        Signal.status.in_(["READY", "TRIGGERED"])).first() is not None


def load_news_events(session, now: datetime | None = None,
                     window_hours: int = 2) -> list[dict]:
    """Upcoming/recent scheduled events for the blackout filter
    (worker writes economic_events; engine only reads)."""
    now = now or _now()
    lo = now - timedelta(hours=window_hours)
    hi = now + timedelta(hours=window_hours)
    rows = (session.query(EconomicEvent)
            .filter(EconomicEvent.scheduledAt >= lo, EconomicEvent.scheduledAt <= hi)
            .all())
    out = []
    for r in rows:
        when = r.scheduledAt
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        out.append({"scheduled_at": when, "impact": r.impact, "title": r.title})
    return out


def active_sides(session) -> list[str]:
    rows = session.query(Signal).filter(Signal.status.in_(["READY", "TRIGGERED"])).all()
    return [r.side.lower() for r in rows]


def save_analysis(session, symbol: str, snapshot: dict) -> Analysis:
    sym = ensure_symbol(session, symbol)
    row = Analysis(
        symbolId=sym.id, priceAtAnalysis=snapshot["price"],
        priceSource=snapshot.get("price_source", "binance"),
        bias=snapshot["bias"], regime=REGIME_MAP.get(snapshot.get("regime", ""), "UNKNOWN"),
        adx=snapshot.get("adx"), atr=snapshot.get("atr"),
        structureJson=snapshot.get("structure"), poiJson=snapshot.get("poi"),
        btcContextJson=snapshot.get("btc_context"),
        enrichmentJson=snapshot.get("enrichment"))
    session.add(row)
    session.flush()
    return row


def save_signal(session, candidate, analysis_id: str | None, validity_hours: int = 48) -> Signal:
    from app.core.risk import rr as _rr
    sym = ensure_symbol(session, candidate.symbol)
    entry_mid = (candidate.entry_zone_low + candidate.entry_zone_high) / 2
    row = Signal(
        analysisId=analysis_id, symbolId=sym.id, strategy=candidate.strategy,
        side=candidate.side.upper(), status=candidate.status, score=candidate.score,
        scoreBreakdown=candidate.score_breakdown, grade=candidate.grade,
        regime=REGIME_MAP.get(candidate.regime, "UNKNOWN"),
        entryZoneLow=candidate.entry_zone_low, entryZoneHigh=candidate.entry_zone_high,
        stopLoss=candidate.stop_loss, tp1=candidate.tp1, tp2=candidate.tp2,
        rrTp1=_rr(entry_mid, candidate.stop_loss, candidate.tp1),
        rrTp2=_rr(entry_mid, candidate.stop_loss, candidate.tp2),
        invalidationPrice=candidate.invalidation,
        reasonAr=candidate.reason_ar, reasonEn=candidate.reason_en,
        readyAt=_now() if candidate.status == "READY" else None,
        expiresAt=_now() + timedelta(hours=validity_hours))
    session.add(row)
    session.flush()
    session.add(SignalOutcome(signalId=row.id, result="OPEN"))
    return row


def start_run(session) -> EngineRun:
    run = EngineRun(status="running")
    session.add(run)
    session.flush()
    return run


def finish_run(session, run: EngineRun, scanned: int, created: int, errors: list) -> None:
    run.finishedAt = _now()
    run.symbolsScanned = scanned
    run.signalsCreated = created
    run.errorsJson = errors
    run.status = "completed" if not errors else "completed_with_errors"


def track_outcomes(session, latest: dict[str, list[dict]], fee_r: float = 0.06,
                   slip_r: float = 0.03, partial: float = 0.5) -> list[dict]:
    """Advance open signals using newest closed 15m candles.
    SL-first rule: if SL and TP touched in same candle, SL wins."""
    updates = []
    open_signals = session.query(Signal).filter(
        Signal.status.in_(["READY", "TRIGGERED"])).all()
    for sig in open_signals:
        sym = session.query(Symbol).filter_by(id=sig.symbolId).first()
        candles = latest.get(sym.symbol if sym else "", [])
        if not candles:
            continue
        outcome = sig.outcome or SignalOutcome(signalId=sig.id)
        entry = sig.entryPrice or (sig.entryZoneLow + sig.entryZoneHigh) / 2
        risk = abs(entry - sig.stopLoss) or 1e-9
        side = sig.side.lower()
        # Trigger when price enters the entry zone
        if sig.status == "READY":
            last = candles[-1]
            if last["l"] <= sig.entryZoneHigh and last["h"] >= sig.entryZoneLow:
                sig.status = "TRIGGERED"
                sig.entryPrice = entry
                sig.triggeredAt = _now()
                updates.append({"signal": sig.id, "event": "TRIGGERED"})
        if sig.status != "TRIGGERED":
            if sig.expiresAt and _now() > sig.expiresAt:
                sig.status, outcome.result = "INVALIDATED", "EXPIRED"
                outcome.closedAt = _now()
                updates.append({"signal": sig.id, "event": "EXPIRED"})
            continue
        bar = candles[-1]
        hit_sl = bar["h"] >= sig.stopLoss if side == "short" else bar["l"] <= sig.stopLoss
        hit_tp1 = bar["l"] <= sig.tp1 if side == "short" else bar["h"] >= sig.tp1
        hit_tp2 = bar["l"] <= sig.tp2 if side == "short" else bar["h"] >= sig.tp2
        r1 = abs(sig.tp1 - entry) / risk
        r2 = abs(sig.tp2 - entry) / risk
        partial_taken = outcome.notes == "TP1_TAKEN"
        event = None
        realized = None
        if not partial_taken:
            if hit_sl:
                realized, event = -1.0, "LOSS_SL"
            elif hit_tp2:
                realized, event = r2, "WIN_TP2"
            elif hit_tp1:
                outcome.notes = "TP1_TAKEN"
                sig.stopLoss = entry  # move to break-even
                updates.append({"signal": sig.id, "event": "TP1_BE"})
                continue
        else:
            if hit_sl:
                realized, event = partial * r1, "WIN_TP1_BE"
            elif hit_tp2:
                realized, event = partial * r1 + (1 - partial) * r2, "WIN_TP2"
        if event:
            realized -= fee_r + slip_r
            sig.status, sig.closedAt = "CLOSED", _now()
            outcome.result, outcome.realizedR = event, round(realized, 4)
            outcome.exitPrice = bar["c"]
            outcome.closedAt = _now()
            if sig.triggeredAt:
                outcome.durationMinutes = int((_now() - sig.triggeredAt).total_seconds() // 60)
            updates.append({"signal": sig.id, "event": event, "r": outcome.realizedR})
    return updates


def list_signals(session, status: str | None = None, limit: int = 50) -> list[dict]:
    q = session.query(Signal).order_by(Signal.createdAt.desc())
    if status:
        q = q.filter(Signal.status == status)
    out = []
    for s in q.limit(limit).all():
        sym = session.query(Symbol).filter_by(id=s.symbolId).first()
        out.append({
            "id": s.id, "symbol": sym.symbol if sym else None, "strategy": s.strategy,
            "side": s.side, "status": s.status, "score": s.score, "grade": s.grade,
            "entry_zone": [s.entryZoneLow, s.entryZoneHigh], "stop_loss": s.stopLoss,
            "tp1": s.tp1, "tp2": s.tp2, "rr_tp1": s.rrTp1, "rr_tp2": s.rrTp2,
            "reason_ar": s.reasonAr, "reason_en": s.reasonEn,
            "outcome": ({"result": s.outcome.result, "realized_r": s.outcome.realizedR}
                        if s.outcome else None),
            "created_at": s.createdAt.isoformat() if s.createdAt else None,
        })
    return out


def closed_outcomes(session) -> list[dict]:
    rows = session.query(SignalOutcome).filter(
        SignalOutcome.result.in_(["WIN_TP2", "WIN_TP1_BE", "LOSS_SL"])).all()
    out = []
    for o in rows:
        sig = o.signal
        sym = session.query(Symbol).filter_by(id=sig.symbolId).first() if sig else None
        out.append({"strategy": sig.strategy if sig else "?",
                    "symbol": sym.symbol if sym else "?",
                    "regime": sig.regime if sig else "UNKNOWN",
                    "side": sig.side if sig else "?",
                    "score": sig.score if sig else 0,
                    "score_breakdown": sig.scoreBreakdown if sig else {},
                    "r": o.realizedR or 0.0, "result": o.result})
    return out
