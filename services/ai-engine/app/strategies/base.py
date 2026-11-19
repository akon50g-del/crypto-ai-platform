"""Base strategy contract. Adding a strategy = one new file subclassing
BaseStrategy + one entry in config/strategies.json. No other code changes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SignalCandidate:
    symbol: str
    strategy: str            # A | B | C | D
    side: str                # long | short
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    tp1: float
    tp2: float
    invalidation: float | None = None
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    grade: str = "REJECTED"
    status: str = "NO_SETUP"  # NO_SETUP | WATCH | READY
    regime: str = "unknown"
    reason_ar: str = ""
    reason_en: str = ""
    context: dict = field(default_factory=dict)  # audit snapshot (structure/poi/btc)


@dataclass
class MarketContext:
    """Multi-timeframe input for one symbol. All candle lists: CLOSED only,
    oldest first."""
    symbol: str
    candles: dict[str, list[dict]]   # timeframe -> candles (4h, 1h, 15m, ...)
    btc_candles_4h: list[dict] = field(default_factory=list)
    btc_bias: str = "range"
    news_events: list[dict] = field(default_factory=list)
    has_active_signal: bool = False

    def tf(self, name: str) -> list[dict]:
        return self.candles.get(name, [])


class BaseStrategy(ABC):
    code: str = "?"
    name: str = "Base"

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def evaluate(self, ctx: MarketContext) -> SignalCandidate | None:
        """Return a candidate (possibly WATCH/REJECTED for learning) or None."""
        raise NotImplementedError
