"""Exchange-aware OHLCV loading for journal analysis.

Journal positions must be evaluated with the market they were traded on whenever
that exchange exposes compatible public candles.  Binance Spot remains a
clearly-labelled fallback for unavailable exchange data or unsupported bars.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import pandas as pd
import requests

from backend.config.settings import TIMEFRAME_TO_MINUTES, get_deepcoin_api_base_url
from backend.utils.data_service import cached, fetch_binance_klines

logger = logging.getLogger(__name__)

DEEPCOIN_CANDLES_PATH = "/deepcoin/v2/market/candles"
DEEPCOIN_MAX_CANDLES_PER_REQUEST = 300
DEEPCOIN_BAR_BY_INTERVAL = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "4h": "4H",
    "12h": "12H",
    "1d": "1D",
    "1w": "1W",
    "1M": "1M",
}
DEEPCOIN_SOURCE = "Deepcoin SWAP API"
BINANCE_FALLBACK_SOURCE = "Binance Spot fallback"
NON_MINUTE_INTERVAL_MS = {
    "1w": 7 * 24 * 60 * 60 * 1000,
    # The last monthly candle has no following open timestamp. A conservative
    # 31-day close keeps it out of point-in-time features until it is certainly complete.
    "1M": 31 * 24 * 60 * 60 * 1000,
}


def _deepcoin_instrument_id(symbol: str) -> Optional[str]:
    normalized = symbol.replace("/", "-").upper().strip()
    if not normalized or "-" not in normalized:
        return None
    base, quote = normalized.split("-", 1)
    if not base or not quote:
        return None
    return f"{base}-{quote}-SWAP"


def _interval_ms(interval: str) -> Optional[int]:
    minutes = TIMEFRAME_TO_MINUTES.get(interval)
    return minutes * 60 * 1000 if minutes is not None else NON_MINUTE_INTERVAL_MS.get(interval)


def _normalize_deepcoin_rows(rows: list[object], interval: str) -> Optional[pd.DataFrame]:
    interval_ms = _interval_ms(interval)
    if interval_ms is None:
        return None
    normalized = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            continue
        try:
            open_time = int(float(row[0]))
            normalized.append({
                "open_time": open_time,
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "quote_volume": float(row[6]),
                "close_time": open_time + interval_ms - 1,
                "trade_count": 0,
            })
        except (TypeError, ValueError):
            continue
    if not normalized:
        return None
    frame = pd.DataFrame(normalized).drop_duplicates(subset=["open_time"])
    frame.sort_values("open_time", inplace=True)
    frame.reset_index(drop=True, inplace=True)
    next_open_time = frame["open_time"].shift(-1)
    frame["close_time"] = next_open_time.sub(1).fillna(frame["open_time"] + interval_ms - 1).astype("int64")
    frame["open_dt"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    return frame


@cached(ttl_seconds=30)
def fetch_deepcoin_swap_klines(
    symbol: str,
    timeframe: str,
    total_candles: int = 1_000,
    end_time: Optional[int] = None,
) -> Optional[pd.DataFrame]:
    """Fetch paginated public Deepcoin SWAP candles, newest window first."""
    bar = DEEPCOIN_BAR_BY_INTERVAL.get(timeframe)
    instrument_id = _deepcoin_instrument_id(symbol)
    if bar is None or instrument_id is None:
        return None

    remaining = max(1, int(total_candles))
    cursor = int(end_time) if end_time is not None else None
    collected: list[object] = []
    base_url = get_deepcoin_api_base_url().rstrip("/")
    try:
        while remaining > 0:
            params = {
                "instId": instrument_id,
                "bar": bar,
                "limit": min(DEEPCOIN_MAX_CANDLES_PER_REQUEST, remaining),
            }
            if cursor is not None:
                params["endTime"] = cursor
            response = requests.get(
                f"{base_url}{DEEPCOIN_CANDLES_PATH}",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or str(payload.get("code", "0")) not in {"0", "None"}:
                return None
            batch = payload.get("data")
            if not isinstance(batch, list) or not batch:
                break
            collected.extend(batch)
            timestamps = [int(float(row[0])) for row in batch if isinstance(row, list) and row]
            if not timestamps:
                break
            remaining -= len(batch)
            cursor = min(timestamps) - 1
            if len(batch) < params["limit"]:
                break
            if remaining > 0:
                time.sleep(0.08)
    except (requests.RequestException, TypeError, ValueError) as exc:
        logger.info("Deepcoin candle request failed for %s %s: %s", symbol, timeframe, exc)
        return None

    frame = _normalize_deepcoin_rows(collected, timeframe)
    return frame.tail(max(1, int(total_candles))).reset_index(drop=True) if frame is not None else None


def _with_source(frame: pd.DataFrame, source: str, fallback: bool) -> pd.DataFrame:
    output = frame.copy()
    output.attrs["market_source"] = source
    output.attrs["market_source_fallback"] = fallback
    return output


def load_journal_ohlcv(
    symbol: str,
    timeframe: str,
    *,
    total_candles: int,
    end_time: Optional[int] = None,
    exchange: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """Load exchange-native candles when available, otherwise Binance Spot.

    The registry is deliberately narrow today: journal imports are Deepcoin
    positions, while future exchange importers can add a provider without
    changing analytical callers.
    """
    if str(exchange or "").strip().lower() == "deepcoin":
        native = fetch_deepcoin_swap_klines(symbol, timeframe, total_candles, end_time)
        if native is not None and not native.empty:
            return _with_source(native, DEEPCOIN_SOURCE, False)

    fallback = fetch_binance_klines(symbol.replace("/", ""), timeframe, total_candles, end_time)
    if fallback is None or fallback.empty:
        return None
    return _with_source(fallback, BINANCE_FALLBACK_SOURCE, True)


def market_source(frame: Optional[pd.DataFrame]) -> str:
    return str(frame.attrs.get("market_source") or "Unknown market data") if frame is not None else "Unknown market data"


def is_market_fallback(frame: Optional[pd.DataFrame]) -> bool:
    return bool(frame is not None and frame.attrs.get("market_source_fallback"))


__all__ = [
    "BINANCE_FALLBACK_SOURCE",
    "DEEPCOIN_SOURCE",
    "fetch_deepcoin_swap_klines",
    "is_market_fallback",
    "load_journal_ohlcv",
    "market_source",
]
