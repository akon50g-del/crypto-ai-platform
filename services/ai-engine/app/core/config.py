"""Loads config/strategies.json (single source of truth) with safe defaults.

Every tunable from STRATEGY_SPEC lives in that JSON file so strategies can be
enabled/disabled and thresholds changed without touching code.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

DEFAULTS: dict = {
    "version": "1.0.0",
    "scan": {
        "intervalMinutes": 5,
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT",
                    "BNBUSDT", "DOGEUSDT", "LINKUSDT", "AVAXUSDT"],
        "timeframes": {"bias": "4h", "entryZone": "1h", "confirmation": "15m",
                       "context": "1d", "execution": ["5m", "1m"]},
        "maxCorrelatedSignals": 2,
        "minMinutesBetweenAlertsPerSymbol": 60,
        "preferredSessions": ["london", "new_york"],
    },
    "structure": {
        "swingN": 2, "swingNSmallTimeframe": 3,
        "displacementMultiplier": 1.5, "displacementLookback": 20,
        "equalLevelTolerancePct": 0.15,
        "ote": {"low": 0.62, "high": 0.79},
        "fiboAlt": {"low": 0.70, "high": 0.85, "requiresIdmSweep": True},
    },
    "scoring": {
        "weights": {"bias": 2, "poi": 2, "sweep": 1, "mss": 2,
                    "ltfConfirmation": 1, "liquidityTarget": 1, "rr": 1},
        "thresholds": {"execute": 7, "watch": 5},
        "grades": {"Aplus": 8, "A": 7},
    },
    "risk": {
        "riskPerTradePct": 1.0, "maxRiskPerTradePct": 2.0,
        "dailyLossLimitPct": 2.0, "stopAfterConsecutiveLosses": 2,
        "minFinalRR": 2.0, "slAtrBuffer": [0.1, 0.2],
        "tp1PartialPct": 50, "tp1RRange": [1.0, 1.5], "tp2R": 2.5,
        "leverageRange": [2, 3], "marginMode": "isolated",
        "pendingOrderValidityHours": [24, 48],
        "backtest": {"feeR": 0.06, "slipR": 0.03, "partial": 0.5, "rr1": 1.25, "rr2": 2.5},
    },
    "strategies": {
        "A": {"enabled": True, "name": "ICT Continuation"},
        "B": {"enabled": True, "name": "Liquidity Sweep Reversal"},
        "C": {"enabled": True, "name": "Trend Pullback / Breakout Retest", "adxMin": 20, "minCandles": 230},
        "D": {"enabled": True, "name": "Mean Reversion (Range)", "adxMax": 20, "minCandles": 60},
    },
    "filters": {"btcContext": True, "newsBlackoutMinutes": 30,
                "atrAnomalyGuard": True, "oneActiveSignalPerSymbol": True},
    "enrichment": {"nansen": {"enabled": False}, "liquidations": {"enabled": False}},
    "learning": {"enabled": True, "minClosedTradesForWeightTuning": 100,
                 "reviewEveryClosedTrades": 20,
                 "acceptance": {"minProfitFactor": 1.2}},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _find_strategies_file() -> Path | None:
    env = os.getenv("STRATEGIES_CONFIG")
    candidates = []
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    candidates += [
        here.parents[3] / "config" / "strategies.json",   # monorepo root
        here.parents[2] / "config" / "strategies.json",
        Path("/app/config/strategies.json"),               # docker mount
        Path.cwd() / "config" / "strategies.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_config() -> dict:
    path = _find_strategies_file()
    if path is None:
        return deepcopy(DEFAULTS)
    try:
        return _deep_merge(DEFAULTS, json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        return deepcopy(DEFAULTS)


CONFIG: dict = load_config()


def database_url() -> str:
    """Postgres in production (Supabase); SQLite default so the engine runs
    locally with zero setup."""
    return os.getenv("DATABASE_URL", "sqlite:///./ai_engine.db")


def binance_base_url() -> str:
    # data-api.binance.vision = public market-data endpoint (same shape as
    # api.binance.com, fewer geo restrictions). Override via BINANCE_BASE_URL.
    return os.getenv("BINANCE_BASE_URL", "https://data-api.binance.vision").rstrip("/")
