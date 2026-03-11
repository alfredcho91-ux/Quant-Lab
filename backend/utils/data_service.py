# utils/data_service.py
"""
Data service functions for fetching market data
This is a standalone version without Streamlit dependencies
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import ccxt
import time
import requests
import logging
import hashlib
import json
from functools import wraps

from utils.cache import DataCache

# 로깅 설정
logger = logging.getLogger(__name__)

# ───────────────── Constants ─────────────────
BINANCE_TFS = [
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h",
    "12h", "1d", "3d", "1w", "1M"
]

BASE_DIR = Path(__file__).parent.parent.parent / "binance_klines"


def _tf_weight(tf: str) -> int:
    """Calculate weight for timeframe sorting"""
    try:
        num = int(tf[:-1])
        unit = tf[-1]
        mult = {"m": 1, "h": 60, "d": 1440, "w": 10080, "M": 43200}
        return num * mult[unit]
    except (ValueError, KeyError, TypeError):
        return 10**9


# Data service cache directory and marker for cached None values
_CACHE_BASE_DIR = Path(__file__).parent.parent.parent / ".cache" / "data_service"
_CACHE_WRAPPER_MARK = "__cache_wrapper_v1__"


def cached(ttl_seconds: int):
    """TTL cache decorator backed by DataCache (diskcache or memory fallback)."""
    def decorator(func):
        cache = DataCache(
            ttl_seconds=ttl_seconds,
            cache_dir=str(_CACHE_BASE_DIR / func.__name__),
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            payload = json.dumps(
                {"args": args, "kwargs": kwargs},
                sort_keys=True,
                default=str,
            )
            cache_key = f"{func.__name__}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"

            cached_entry = cache.get(cache_key)
            if isinstance(cached_entry, dict) and cached_entry.get(_CACHE_WRAPPER_MARK):
                return cached_entry.get("value")

            result = func(*args, **kwargs)
            cache.set(cache_key, {_CACHE_WRAPPER_MARK: True, "value": result})
            return result

        return wrapper

    return decorator


@cached(ttl_seconds=5)
def discover_timeframes(coin_name: str, base_dir: Path = BASE_DIR):
    """Discover available timeframes from CSV files"""
    csv_tfs = set()
    try:
        if base_dir.exists():
            for p in base_dir.glob(f"{coin_name}USDT-*-merged.csv"):
                m = re.match(rf"^{coin_name}USDT-(.+?)-merged\.csv$", p.name, re.I)
                if m:
                    csv_tfs.add(m.group(1))
    except OSError as exc:
        logger.warning("Failed to scan timeframe CSV files for %s: %s", coin_name, exc)
    
    all_tfs = sorted(set(BINANCE_TFS) | csv_tfs, key=_tf_weight)
    return all_tfs, set(BINANCE_TFS), sorted(csv_tfs, key=_tf_weight)


@cached(ttl_seconds=300)
def get_fear_and_greed_index():
    """Get Fear & Greed Index from alternative.me API"""
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5)
        r.raise_for_status()
        payload = r.json()
        return payload["data"][0]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        logger.debug("Fear & Greed API unavailable: %s", exc)
        return None


@cached(ttl_seconds=30)
def get_market_prices():
    """Get market prices from Binance"""
    try:
        ex = ccxt.binance()
        return ex.fetch_tickers(["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
    except ccxt.BaseError as exc:
        logger.debug("Binance ticker API unavailable: %s", exc)
        return None


def fetch_live_data(symbol: str, timeframe: str, limit: int = 1000, total_candles: int = 3000):
    """Fetch live OHLCV data from Binance API with pagination"""
    try:
        # 주봉(1w): 모든 페이지에서 API 조회 시 최근 300개만 사용
        if timeframe == "1w":
            total_candles = min(total_candles, 300)
        ex = ccxt.binance()
        tf_ms = ex.parse_timeframe(timeframe) * 1000
        now = ex.milliseconds()
        since = now - (total_candles * tf_ms)
        
        all_ohlcv = []
        cur = since
        
        for _ in range(15):
            if cur >= now:
                break
            try:
                o = ex.fetch_ohlcv(symbol, timeframe, since=cur, limit=limit)
            except ccxt.BaseError as exc:
                logger.debug(
                    "fetch_ohlcv retry for %s %s since=%s failed: %s",
                    symbol,
                    timeframe,
                    cur,
                    exc,
                )
                time.sleep(1)
                continue
            
            if not o:
                break
            
            all_ohlcv.extend(o)
            cur = o[-1][0] + 1
            
            if len(all_ohlcv) >= total_candles:
                break
            
            time.sleep(0.1)
        
        if not all_ohlcv:
            return None
        
        df = pd.DataFrame(
            all_ohlcv,
            columns=["open_time", "open", "high", "low", "close", "volume"],
        )
        df["open_dt"] = pd.to_datetime(df["open_time"], unit="ms")
        df.sort_values("open_dt", inplace=True)
        df.drop_duplicates(subset=["open_time"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        if timeframe == "1w" and len(df) > 300:
            df = df.tail(300).reset_index(drop=True)
        return df
    except (ccxt.BaseError, ValueError, TypeError) as exc:
        logger.error("API Error while loading %s %s: %s", symbol, timeframe, exc)
        return None
    except Exception as exc:
        logger.exception("Unexpected API error while loading %s %s: %s", symbol, timeframe, exc)
        return None


def load_csv_data(coin_name: str, interval: str, base_dir: Path = BASE_DIR):
    """Load historical data from local CSV files"""
    # coin_name에서 USDT 접미사 제거 (중복 방지)
    coin_name = coin_name.replace("USDT", "").replace("usdt", "")
    
    # interval 매핑 (API 표기 → CSV 파일명 표기)
    interval_map = {
        "1M": "1mo",  # 월봉: API는 1M, CSV는 1mo
    }
    csv_interval = interval_map.get(interval, interval)
    
    fp = base_dir / f"{coin_name}USDT-{csv_interval}-merged.csv"
    
    if not fp.exists():
        return None, str(fp)
    
    try:
        df = pd.read_csv(fp)
        df.columns = df.columns.str.strip().str.lower()
        
        ot = pd.to_numeric(df["open_time"], errors="coerce")
        if (ot > 2_000_000_000_000).any():
            ot = np.where(ot > 2_000_000_000_000, ot // 1000, ot)
        
        df["open_time"] = ot
        df["open_dt"] = pd.to_datetime(df["open_time"], unit="ms")
        df.sort_values("open_dt", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df, "CSV file"
    except (OSError, pd.errors.ParserError, ValueError, KeyError) as exc:
        logger.warning("Failed to load CSV data from %s: %s", fp, exc)
        return None, "Error"
