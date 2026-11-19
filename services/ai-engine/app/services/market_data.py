"""Market data: Binance public REST (primary) + CoinGecko (fallback price).

Rules from the Skills: never invent wicks/levels; closed candles only
(the forming candle is dropped); every price carries source + UTC time.
No API key needed for Binance klines/ticker public endpoints.
"""
from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import os

import httpx

from app.core.config import binance_base_url

INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d"}
COINGECKO_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple",
                 "BNB": "binancecoin", "DOGE": "dogecoin", "LINK": "chainlink",
                 "AVAX": "avalanche-2"}




def _client(timeout: int) -> httpx.Client:
    # Explicit proxy (if the host sets one) + trust_env=False: avoids broken
    # NO_PROXY parsing in some environments while still honoring egress proxies.
    proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY") or None
    verify = os.getenv("SSL_CERT_FILE") or True
    return httpx.Client(timeout=timeout, trust_env=False, proxy=proxy, verify=verify)

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_klines(symbol: str, interval: str, limit: int = 300,
                 client: httpx.Client | None = None) -> list[dict]:
    """Closed OHLCV candles, oldest first. Drops the still-forming last candle."""
    if interval not in INTERVALS:
        raise ValueError(f"unsupported interval {interval}")
    own = client is None
    client = client or _client(20)
    try:
        resp = client.get(f"{binance_base_url()}/api/v3/klines",
                          params={"symbol": symbol, "interval": interval, "limit": limit})
        resp.raise_for_status()
        rows = resp.json()
    finally:
        if own:
            client.close()
    candles = [{"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]),
                "c": float(r[4]), "v": float(r[5])} for r in rows]
    return candles[:-1] if len(candles) > 1 else candles  # drop forming candle


def fetch_ticker(symbol: str, client: httpx.Client | None = None) -> dict:
    own = client is None
    client = client or _client(15)
    try:
        resp = client.get(f"{binance_base_url()}/api/v3/ticker/price",
                          params={"symbol": symbol})
        resp.raise_for_status()
        data = resp.json()
        return {"symbol": symbol, "price": float(data["price"]),
                "source": "binance", "time_utc": _now_iso()}
    finally:
        if own:
            client.close()


def fetch_coingecko_price(symbol: str, client: httpx.Client | None = None) -> dict:
    """Fallback live price (close-only source — zones from it are approximate
    ±1-2% and must be disclosed, per the Skills)."""
    base = symbol.replace("USDT", "")
    coin_id = COINGECKO_IDS.get(base)
    if not coin_id:
        raise ValueError(f"no CoinGecko id for {symbol}")
    own = client is None
    client = client or _client(15)
    try:
        resp = client.get("https://api.coingecko.com/api/v3/simple/price",
                          params={"ids": coin_id, "vs_currencies": "usd"})
        resp.raise_for_status()
        price = float(resp.json()[coin_id]["usd"])
        return {"symbol": symbol, "price": price, "source": "coingecko",
                "time_utc": _now_iso(), "note": "close-only source; zones approximate ±1-2%"}
    finally:
        if own:
            client.close()


def fetch_live_price(symbol: str) -> dict:
    try:
        return fetch_ticker(symbol)
    except Exception:
        return fetch_coingecko_price(symbol)


def load_csv_candles(text: str) -> list[dict]:
    """Parse time,open,high,low,close[,volume] CSV (oldest or newest first).
    Duplicate timestamps are rejected — they corrupt results (Skills rule)."""
    rows = list(csv.DictReader(io.StringIO(text)))
    candles = []
    for r in rows:
        candles.append({"t": r.get("time", ""), "o": float(r["open"]), "h": float(r["high"]),
                        "l": float(r["low"]), "c": float(r["close"]),
                        "v": float(r.get("volume", 0) or 0)})
    def key(c):
        s = str(c["t"]).strip()
        try:
            x = float(s)
            return x / 1000.0 if x > 1e11 else x
        except ValueError:
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
    keys = [key(c) for c in candles]
    if candles and all(k is not None for k in keys):
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate candle timestamps in CSV")
        candles = [c for _, c in sorted(zip(keys, candles), key=lambda x: x[0])]
    return candles


class CandleCache:
    """Tiny in-process TTL cache (Redis replaces this in production deploys)."""

    def __init__(self, ttl_seconds: int = 120):
        self.ttl = ttl_seconds
        self._store: dict[tuple[str, str], tuple[float, list[dict]]] = {}

    def get(self, symbol: str, interval: str, limit: int = 300) -> list[dict]:
        key = (symbol, interval)
        hit = self._store.get(key)
        if hit and time.time() - hit[0] < self.ttl:
            return hit[1][-limit:]
        data = fetch_klines(symbol, interval, limit)
        self._store[key] = (time.time(), data)
        return data
