"""AI Engine API (FastAPI). Run: uvicorn app.main:app --port 8000

Endpoints: /health /config /scan /analyze/{symbol} /signals /backtest /stats
Internal endpoints (scan/signals/outcomes) accept X-Internal-Token when
AI_ENGINE_INTERNAL_TOKEN is set. Scheduler scans every N minutes (config).
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import CONFIG
from app.indicators.technicals import HAS_TALIB
from app.models.db import get_session, init_db
from app.services import learning, repository as repo
from app.services.backtest import run_all, run_backtest, split_in_out
from app.services.market_data import fetch_klines, load_csv_candles
from app.services.scanner import analyze_symbol, run_scan

_scheduler = None


def _check_token(token: str | None) -> None:
    expected = os.getenv("AI_ENGINE_INTERNAL_TOKEN", "")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="invalid internal token")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    global _scheduler
    if os.getenv("DISABLE_SCHEDULER") != "1":
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(run_scan, "interval",
                           minutes=CONFIG["scan"]["intervalMinutes"],
                           id="market_scan", max_instances=1)
        _scheduler.start()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="Crypto AI Engine", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-engine", "talib": HAS_TALIB,
            "scan_interval_minutes": CONFIG["scan"]["intervalMinutes"]}


@app.get("/config")
def get_config():
    return CONFIG


@app.post("/scan")
def scan(x_internal_token: str | None = Header(default=None)):
    _check_token(x_internal_token)
    return run_scan()


@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    symbol = symbol.upper()
    if symbol not in CONFIG["scan"]["symbols"]:
        raise HTTPException(status_code=404, detail="symbol not in approved list")
    out = analyze_symbol(symbol)
    return {
        "symbol": symbol, "snapshot": out["snapshot"],
        "candidates": [{
            "strategy": c.strategy, "side": c.side, "status": c.status,
            "score": c.score, "grade": c.grade, "score_breakdown": c.score_breakdown,
            "entry_zone": [c.entry_zone_low, c.entry_zone_high],
            "stop_loss": c.stop_loss, "tp1": c.tp1, "tp2": c.tp2,
            "invalidation": c.invalidation, "reason_ar": c.reason_ar,
            "reason_en": c.reason_en, "context": c.context,
        } for c in out["candidates"]],
    }


@app.get("/signals")
def signals(status: str | None = None, limit: int = 50):
    session = get_session()
    try:
        return {"signals": repo.list_signals(session, status, limit)}
    finally:
        session.close()


class BacktestRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    mode: str = "all"          # A | B | C | D | all
    limit: int = 1000
    require_volume: bool = False


@app.post("/backtest")
def backtest(req: BacktestRequest, x_internal_token: str | None = Header(default=None)):
    _check_token(x_internal_token)
    candles = fetch_klines(req.symbol.upper(), req.timeframe, req.limit)
    bt = CONFIG["risk"]["backtest"]
    kwargs = {"fee_r": bt["feeR"], "slip_r": bt["slipR"], "partial": bt["partial"],
              "rr1": bt["rr1"], "rr2": bt["rr2"], "require_volume": req.require_volume}
    in_sample, out_sample = split_in_out(candles)
    def slim(r):
        return {k: v for k, v in r.items() if k != "trades_detail"}
    if req.mode == "all":
        return {"symbol": req.symbol, "timeframe": req.timeframe, "candles": len(candles),
                "full": {m: slim(r) for m, r in run_all(candles, **kwargs).items()},
                "out_of_sample": {m: slim(r) for m, r in run_all(out_sample, **kwargs).items()}
                if len(out_sample) >= 230 else "insufficient OOS candles"}
    return {"symbol": req.symbol, "timeframe": req.timeframe, "candles": len(candles),
            "full": slim(run_backtest(candles, req.mode.upper(), **kwargs)),
            "out_of_sample": slim(run_backtest(out_sample, req.mode.upper(), **kwargs))
            if len(out_sample) >= 230 else "insufficient OOS candles"}


@app.post("/backtest/csv")
async def backtest_csv(mode: str = "all", file: UploadFile = File(...),
                       x_internal_token: str | None = Header(default=None)):
    _check_token(x_internal_token)
    text = (await file.read()).decode("utf-8")
    candles = load_csv_candles(text)
    bt = CONFIG["risk"]["backtest"]
    kwargs = {"fee_r": bt["feeR"], "slip_r": bt["slipR"], "partial": bt["partial"],
              "rr1": bt["rr1"], "rr2": bt["rr2"]}
    if mode == "all":
        return {"candles": len(candles),
                "results": {m: {k: v for k, v in r.items() if k != "trades_detail"}
                            for m, r in run_all(candles, **kwargs).items()}}
    r = run_backtest(candles, mode.upper(), **kwargs)
    return {"candles": len(candles),
            "result": {k: v for k, v in r.items() if k != "trades_detail"}}


@app.get("/stats")
def stats():
    session = get_session()
    try:
        outcomes = repo.closed_outcomes(session)
    finally:
        session.close()
    return {"stats": learning.aggregate(outcomes),
            "weight_suggestion": learning.suggest_weights(
                outcomes, CONFIG["learning"]["minClosedTradesForWeightTuning"])}
