"""
데이터 로딩, 인덱스 처리 및 기술적 지표 계산
"""
import pandas as pd
import numpy as np
import logging
from typing import Optional, Tuple, Any, List, Literal
import os

from utils.data_service import fetch_live_data, load_csv_data
from .cache_ops import data_cache, indicators_cache

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv('DEBUG_STREAK_ANALYSIS', 'False').lower() in ('true', '1', 'yes')
DEFAULT_RSI = 50.0
REQUIRED_INDICATOR_COLUMNS = {"atr_pct", "rsi", "disparity", "ema_200"}

def normalize_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 인덱스를 DatetimeIndex로 강제 정규화
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    if isinstance(df.index, pd.DatetimeIndex):
        return df
    
    if 'open_dt' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['open_dt']):
            df['open_dt'] = pd.to_datetime(df['open_dt'])
        df = df.set_index('open_dt')
        logger.debug("DatetimeIndex 설정 완료 (open_dt 컬럼 사용)")
        return df
    
    if 'open_time' in df.columns:
        ot = df['open_time']
        if pd.api.types.is_numeric_dtype(ot):
            max_val = ot.max()
            if max_val > 2_000_000_000_000:
                ot = ot // 1000 if max_val > 2_000_000_000_000_000 else ot
            df['open_dt'] = pd.to_datetime(ot, unit='ms')
        else:
            df['open_dt'] = pd.to_datetime(ot)
        df = df.set_index('open_dt')
        logger.debug("DatetimeIndex 설정 완료 (open_time 컬럼 변환)")
        return df
    
    logger.warning(f"DatetimeIndex 설정 실패: open_dt, open_time 컬럼 없음 (columns: {df.columns.tolist()})")
    return df


def load_data(coin: str, interval: str) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    데이터 로드 (캐시 -> CSV -> API 순)
    """
    cache_key = f"{coin}_{interval}"
    
    cached = data_cache.get(cache_key)
    if cached is not None:
        return cached, True
    
    df, _ = load_csv_data(coin, interval)
    if df is None or df.empty:
        candle_counts = {'4h': 3000, '1w': 500}
        total_candles = candle_counts.get(interval, 2000)
        df = fetch_live_data(f"{coin}/USDT", interval, total_candles=total_candles)
    
    if df is not None and not df.empty:
        df = normalize_datetime_index(df)
        data_cache.set(cache_key, df)
    
    return df, False


def prepare_dataframe(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    """
    기본 파생 컬럼 추가 (is_green, body_pct 등)
    """
    df = df.copy()
    
    if not isinstance(df.index, pd.DatetimeIndex):
        df = normalize_datetime_index(df)
    
    df['is_green'] = df['close'] > df['open']
    df['is_red'] = df['close'] < df['open']
    
    is_bullish = direction == "green"
    
    if is_bullish:
        df['target_bit'] = df['is_green']
        df['body_pct'] = (df['close'] - df['open']) / df['open'] * 100
    else:
        df['target_bit'] = df['is_red']
        df['body_pct'] = (df['open'] - df['close']) / df['open'] * 100
    
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산 (RSI, ATR, Disparity)"""
    df = df.copy()
    
    # ATR
    df['prev_close'] = df['close'].shift(1)
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['prev_close']).abs(),
        (df['low'] - df['prev_close']).abs()
    ], axis=1).max(axis=1)
    df['atr_14'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = df['atr_14'] / df['close'] * 100
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Disparity
    df['vol_change'] = df['volume'].pct_change() * 100
    df['ma20'] = df['close'].rolling(20).mean()
    df['disparity'] = (df['close'] / df['ma20']) * 100

    # EMA 200 (일봉 고정): 분석 interval과 무관하게 1D 종가 기준으로 계산
    daily_close = df['close'].resample('1D').last().dropna()
    if daily_close.empty:
        df['ema_200'] = np.nan
    else:
        daily_ema_200 = daily_close.ewm(span=200, adjust=False).mean()
        df['ema_200'] = daily_ema_200.reindex(df.index.normalize()).to_numpy()

    return df


def get_or_calculate_indicators(coin: str, interval: str, df: pd.DataFrame) -> pd.DataFrame:
    """지표 계산 (캐싱 적용)"""
    cache_key = f"indicators_{coin}_{interval}"
    
    cached = indicators_cache.get(cache_key)
    if cached is not None and REQUIRED_INDICATOR_COLUMNS.issubset(cached.columns):
        logger.debug(f"Indicators cache hit: {cache_key}")
        return cached
    
    logger.debug(f"Indicators cache miss: {cache_key}, calculating...")
    df_with_indicators = calculate_indicators(df)
    
    indicators_cache.set(cache_key, df_with_indicators)
    logger.debug(f"Indicators cached: {cache_key}")
    
    return df_with_indicators


def filter_rows_by_ema_200_position(
    df: pd.DataFrame,
    rows: pd.DataFrame,
    ema_200_position: Optional[Literal["above", "below"]],
) -> pd.DataFrame:
    """패턴 완성 봉 종가가 EMA 200 위/아래인 행만 유지."""
    if rows is None or rows.empty or ema_200_position is None:
        return rows

    if "ema_200" not in df.columns:
        logger.warning("EMA 200 filter requested but ema_200 column is missing")
        return rows.iloc[0:0].copy()

    eval_df = df.loc[rows.index, ["close", "ema_200"]].dropna()
    if eval_df.empty:
        return rows.iloc[0:0].copy()

    if ema_200_position == "above":
        matched_index = eval_df.index[eval_df["close"] >= eval_df["ema_200"]]
    else:
        matched_index = eval_df.index[eval_df["close"] <= eval_df["ema_200"]]

    if len(matched_index) == 0:
        return rows.iloc[0:0].copy()

    return rows.loc[matched_index].copy()


def normalize_single_index(idx: Any, df_index: pd.Index) -> Optional[Tuple[Any, int]]:
    """단일 인덱스를 정규화하고 위치 찾기"""
    try:
        pos = df_index.get_loc(idx)
        return idx, pos
    except (KeyError, TypeError):
        try:
            if isinstance(df_index, pd.DatetimeIndex):
                if isinstance(idx, pd.Timestamp):
                    idx_normalized = idx
                elif isinstance(idx, str):
                    idx_normalized = pd.to_datetime(idx)
                else:
                    idx_normalized = pd.Timestamp(idx) if not isinstance(idx, pd.Timestamp) else idx
            elif isinstance(idx, str):
                idx_normalized = pd.to_datetime(idx) if isinstance(df_index, pd.DatetimeIndex) else idx
            else:
                idx_normalized = idx
            
            pos = df_index.get_loc(idx_normalized)
            return idx_normalized, pos
        except (KeyError, TypeError, ValueError, pd.errors.ParserError):
            if DEBUG_MODE:
                logger.debug(f"Failed to normalize index: {idx} (type: {type(idx).__name__})")
            return None


def normalize_indices(indices: List[Any], df: pd.DataFrame) -> List[Any]:
    """인덱스 리스트 정규화"""
    normalized = []
    for idx in indices:
        try:
            if isinstance(idx, (int, np.integer)):
                if idx in df.index:
                    normalized.append(idx)
            elif isinstance(idx, str):
                idx_converted = pd.to_datetime(idx)
                if idx_converted in df.index:
                    normalized.append(idx_converted)
            elif isinstance(idx, pd.Timestamp):
                if idx in df.index:
                    normalized.append(idx)
            else:
                try:
                    idx_converted = pd.to_datetime(idx)
                    if idx_converted in df.index:
                        normalized.append(idx_converted)
                except (ValueError, TypeError, pd.errors.ParserError):
                    pass
        except (ValueError, TypeError, pd.errors.ParserError) as e:
            if DEBUG_MODE:
                logger.warning(f"Failed to normalize index: {idx} error: {e}")
            continue
    return normalized


def safe_get_rsi(df: pd.DataFrame, idx: Any, default: float = DEFAULT_RSI) -> float:
    """RSI 값 안전 조회"""
    if 'rsi' not in df.columns:
        return default
    try:
        val = df.loc[idx, 'rsi']
        return float(val) if pd.notna(val) else default
    except (KeyError, IndexError, TypeError, ValueError):
        return default
