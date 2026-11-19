"""SQLAlchemy models — mirror of prisma/schema.prisma (engine-owned subset).

SQLite by default for zero-setup local runs; set DATABASE_URL to Postgres
(Supabase) in production. Prisma remains the migration owner for the API;
these models use the same table/column names so both services share one DB.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, JSON, String, Text, UniqueConstraint, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.core.config import database_url

Base = declarative_base()


def _id() -> str:
    return uuid.uuid4().hex[:25]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(String, primary_key=True, default=_id)
    symbol = Column(String, unique=True, nullable=False)
    baseAsset = Column(String, nullable=False)
    quoteAsset = Column(String, default="USDT")
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime(timezone=True), default=_now)


class CandleRow(Base):
    __tablename__ = "candles"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbolId = Column(String, ForeignKey("symbols.id"), nullable=False)
    timeframe = Column(String, nullable=False)
    openTime = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    source = Column(String, default="binance")
    isClosed = Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("symbolId", "timeframe", "openTime"),)


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=_id)
    symbolId = Column(String, ForeignKey("symbols.id"), nullable=False)
    timeframeBias = Column(String, default="4h")
    priceAtAnalysis = Column(Float, nullable=False)
    priceSource = Column(String, default="binance")
    bias = Column(String, nullable=False)
    regime = Column(String, default="UNKNOWN")
    adx = Column(Float)
    atr = Column(Float)
    structureJson = Column(JSON)
    poiJson = Column(JSON)
    btcContextJson = Column(JSON)
    enrichmentJson = Column(JSON)
    createdAt = Column(DateTime(timezone=True), default=_now)
    signals = relationship("Signal", back_populates="analysis")


class Signal(Base):
    __tablename__ = "signals"
    id = Column(String, primary_key=True, default=_id)
    analysisId = Column(String, ForeignKey("analyses.id"))
    symbolId = Column(String, ForeignKey("symbols.id"), nullable=False)
    strategy = Column(String, nullable=False)
    side = Column(String, nullable=False)  # LONG | SHORT
    status = Column(String, default="WATCH")
    score = Column(Integer, nullable=False)
    scoreBreakdown = Column(JSON, nullable=False)
    grade = Column(String)
    regime = Column(String, default="UNKNOWN")
    entryZoneLow = Column(Float, nullable=False)
    entryZoneHigh = Column(Float, nullable=False)
    entryPrice = Column(Float)
    stopLoss = Column(Float, nullable=False)
    tp1 = Column(Float, nullable=False)
    tp2 = Column(Float, nullable=False)
    rrTp1 = Column(Float)
    rrTp2 = Column(Float)
    invalidationPrice = Column(Float)
    reasonAr = Column(Text, nullable=False)
    reasonEn = Column(Text)
    readyAt = Column(DateTime(timezone=True))
    triggeredAt = Column(DateTime(timezone=True))
    closedAt = Column(DateTime(timezone=True))
    expiresAt = Column(DateTime(timezone=True))
    createdAt = Column(DateTime(timezone=True), default=_now)
    updatedAt = Column(DateTime(timezone=True), default=_now, onupdate=_now)
    analysis = relationship("Analysis", back_populates="signals")
    outcome = relationship("SignalOutcome", back_populates="signal", uselist=False)


class SignalOutcome(Base):
    __tablename__ = "signal_outcomes"
    id = Column(String, primary_key=True, default=_id)
    signalId = Column(String, ForeignKey("signals.id"), unique=True, nullable=False)
    result = Column(String, default="OPEN")
    exitPrice = Column(Float)
    realizedR = Column(Float)
    durationMinutes = Column(Integer)
    maeR = Column(Float)
    mfeR = Column(Float)
    notes = Column(Text)
    closedAt = Column(DateTime(timezone=True))
    createdAt = Column(DateTime(timezone=True), default=_now)
    signal = relationship("Signal", back_populates="outcome")


class EconomicEvent(Base):
    """Mirror of Prisma economic_events (written by the Worker, Phase 5).
    The engine only reads it for the news-blackout filter."""
    __tablename__ = "economic_events"
    id = Column(String, primary_key=True, default=_id)
    title = Column(String, nullable=False)
    currency = Column(String, default="USD")
    impact = Column(String, default="HIGH")
    scheduledAt = Column(DateTime(timezone=True), nullable=False)
    actual = Column(String)
    forecast = Column(String)
    previous = Column(String)
    createdAt = Column(DateTime(timezone=True), default=_now)


class EngineRun(Base):
    __tablename__ = "engine_runs"
    id = Column(String, primary_key=True, default=_id)
    startedAt = Column(DateTime(timezone=True), default=_now)
    finishedAt = Column(DateTime(timezone=True))
    symbolsScanned = Column(Integer, default=0)
    signalsCreated = Column(Integer, default=0)
    errorsJson = Column(JSON)
    status = Column(String, default="running")


_engine = None
_Session = None


def get_engine():
    global _engine, _Session
    if _engine is None:
        url = database_url()
        kwargs: dict = {"future": True}
        if url.startswith("sqlite"):
            # WAL + busy timeout so the scheduler and manual scans don't lock
            # each other out on local SQLite (production uses PostgreSQL).
            kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        _engine = create_engine(url, **kwargs)
        if url.startswith("sqlite"):
            with _engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA journal_mode=WAL")
                conn.exec_driver_sql("PRAGMA busy_timeout=30000")
                conn.commit()
        _Session = sessionmaker(bind=_engine, future=True)
    return _engine


def get_session():
    get_engine()
    return _Session()


def init_db() -> None:
    Base.metadata.create_all(get_engine())
