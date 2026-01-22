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
from functools import lru_cache
from datetime import datetime, timedelta

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
    except Exception:
        return 10**9


# Simple in-memory cache with TTL
_cache = {}
_cache_times = {}


def cached(ttl_seconds: int):
    """Simple TTL cache decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = datetime.now()
            
            if key in _cache and key in _cache_times:
                if (now - _cache_times[key]).total_seconds() < ttl_seconds:
                    return _cache[key]
            
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_times[key] = now
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
    except Exception:
        pass
    
    all_tfs = sorted(set(BINANCE_TFS) | csv_tfs, key=_tf_weight)
    return all_tfs, set(BINANCE_TFS), sorted(csv_tfs, key=_tf_weight)


@cached(ttl_seconds=300)
def get_fear_and_greed_index():
    """Get Fear & Greed Index from alternative.me API"""
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5)
        return r.json()["data"][0]
    except Exception:
        return None


@cached(ttl_seconds=30)
def get_market_prices():
    """Get market prices from Binance"""
    try:
        ex = ccxt.binance()
        return ex.fetch_tickers(["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
    except Exception:
        return None


def fetch_live_data(symbol: str, timeframe: str, limit: int = 1000, total_candles: int = 3000):
    """Fetch live OHLCV data from Binance API with pagination"""
    try:
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
            except Exception:
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
        return df
    except Exception as e:
        logger.error(f"API Error: {e}")
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
    except Exception:
        return None, "Error"

