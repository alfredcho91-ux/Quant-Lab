"""
패턴 매칭, C1 추출 및 품질 분석
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv('DEBUG_STREAK_ANALYSIS', 'False').lower() in ('true', '1', 'yes')

def find_complex_pattern(df: pd.DataFrame, pattern: list = [1, 1, 1, 1, 1, -1, -1]):
    """복합 패턴 매칭 (sliding window 사용)"""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    colors = np.where(
        df['close'] > df['open'], 1,
        np.where(df['close'] < df['open'], -1, 0)
    )
    df['color'] = colors

    pattern_arr = np.asarray(pattern, dtype=np.int8)
    pattern_len = len(pattern_arr)
    if pattern_len == 0 or len(df) < pattern_len:
        return df.iloc[0:0].copy()

    try:
        windows = np.lib.stride_tricks.sliding_window_view(colors, pattern_len)
        matched_window_mask = np.all(windows == pattern_arr, axis=1)
        if not matched_window_mask.any():
            return df.iloc[0:0].copy()
        match_end_positions = np.flatnonzero(matched_window_mask) + pattern_len - 1
        return df.iloc[match_end_positions].copy()
    except AttributeError:
        # numpy < 1.20 fallback
        condition = pd.Series([True] * len(df), index=df.index)
        for i, val in enumerate(pattern_arr):
            condition &= (df['color'].shift(pattern_len - i - 1) == val)
        return df[condition].copy()


def extract_c1_indices(
    df: pd.DataFrame, 
    pattern_indices: pd.Index, 
    filter_green: Optional[bool] = None
) -> List[Any]:
    """패턴 완성 다음 봉(C1) 인덱스 추출"""
    c1_indices = []
    for idx in pattern_indices:
        try:
            pos = df.index.get_loc(idx)
            if pos + 1 < len(df):
                c1_idx = df.index[pos + 1]
                if filter_green is not None:
                    c1_is_green = df.loc[c1_idx, 'is_green']
                    if c1_is_green != filter_green:
                        continue
                c1_indices.append(c1_idx)
        except (KeyError, IndexError, TypeError):
            continue
    return c1_indices


def extract_c1_dates_from_chart_data(
    chart_data: List[Dict[str, Any]], 
    filter_green: Optional[bool] = None
) -> List[pd.Timestamp]:
    """chart_data에서 C1 날짜 추출"""
    c1_dates = []
    for c in chart_data:
        c1_data = c.get('c1')
        if not c1_data:
            continue
        
        if filter_green is not None:
            c1_color = c1_data.get('color')
            expected_color = 1 if filter_green else -1
            if c1_color != expected_color:
                continue
        
        c1_date_str = c1_data.get('date')
        if not c1_date_str:
            continue
        
        try:
            c1_date = pd.to_datetime(c1_date_str)
            c1_dates.append(c1_date)
        except (ValueError, TypeError, pd.errors.ParserError) as e:
            if DEBUG_MODE:
                logger.debug(f"Failed to parse C1 date '{c1_date_str}': {e}")
            continue
    return c1_dates


def analyze_pullback_quality(
    df: pd.DataFrame, 
    pattern_indices: pd.Index, 
    rise_len: int = 5, 
    drop_len: int = 2
) -> List[Dict[str, Any]]:
    """조정 구간 품질 분석 (되돌림, 거래량)"""
    if df is None or df.empty or len(pattern_indices) == 0:
        return []

    results = []
    pattern_len = rise_len + drop_len
    if pattern_len <= 0:
        return results

    has_volume = 'volume' in df.columns
    index_array = pd.Index(pattern_indices)
    positions = df.index.get_indexer(index_array)

    for idx, pos_idx in zip(index_array, positions):
        if pos_idx < 0:
            continue
        try:
            start_pos = pos_idx - pattern_len + 1
            if start_pos < 0:
                continue
            
            pattern_segment = df.iloc[start_pos : pos_idx + 1]
            if len(pattern_segment) == 0:
                continue
            
            first_candle = pattern_segment.iloc[0]
            is_first_green = first_candle['close'] > first_candle['open']
            
            if is_first_green:
                if rise_len > 0 and drop_len > 0:
                    rise_segment = pattern_segment.iloc[:rise_len]
                    drop_segment = pattern_segment.iloc[rise_len:]
                    
                    if len(rise_segment) == 0 or len(drop_segment) == 0:
                        continue
                    
                    rise_start = rise_segment['open'].iloc[0]
                    rise_high = rise_segment['high'].max()
                    drop_end = drop_segment['close'].iloc[-1]
                    
                    rise_range = rise_high - rise_start
                    drop_range = rise_high - drop_end
                    
                    retracement = (drop_range / rise_range * 100) if rise_range > 0 else 0
                    retracement = min(retracement, 100.0)
                    
                    vol_ratio = 1.0
                    if has_volume:
                        vr = rise_segment['volume'].mean()
                        vd = drop_segment['volume'].mean()
                        vol_ratio = (vd / vr) if vr > 0 else 1.0
                else:
                    retracement = 0.0
                    vol_ratio = 1.0
            else:
                if drop_len > 0 and rise_len > 0:
                    drop_segment = pattern_segment.iloc[:drop_len]
                    rise_segment = pattern_segment.iloc[drop_len:]
                    
                    if len(rise_segment) == 0 or len(drop_segment) == 0:
                        continue
                    
                    drop_start = drop_segment['open'].iloc[0]
                    drop_low = drop_segment['low'].min()
                    rise_end = rise_segment['close'].iloc[-1]
                    
                    drop_range = drop_start - drop_low
                    rise_range = rise_end - drop_low
                    
                    retracement = (rise_range / drop_range * 100) if drop_range > 0 else 0
                    retracement = min(retracement, 200.0)
                    
                    vol_ratio = 1.0
                    if has_volume:
                        vd = drop_segment['volume'].mean()
                        vr = rise_segment['volume'].mean()
                        vol_ratio = (vr / vd) if vd > 0 else 1.0
                else:
                    retracement = 0.0
                    vol_ratio = 1.0
            
            results.append({
                'index': idx,
                'retracement_pct': round(retracement, 2),
                'vol_ratio': round(vol_ratio, 2)
            })
        except (KeyError, IndexError, TypeError):
            continue
    
    return results


def calculate_signal_score(retracement_pct: float, vol_ratio: float, rsi: float) -> dict:
    """최종 시그널 점수화"""
    score = 0
    reasons = []
    
    # 지지 강도
    if retracement_pct < 30:
        score += 40
        reasons.append("강력한 지지 (되돌림 < 30%)")
    elif retracement_pct < 50:
        score += 30
        reasons.append("양호한 지지 (되돌림 < 50%)")
    elif retracement_pct < 70:
        score += 15
        reasons.append("보통 지지 (되돌림 < 70%)")
    else:
        reasons.append("약한 지지 (되돌림 >= 70%)")
    
    # 거래량
    if vol_ratio < 0.7:
        score += 30
        reasons.append("건강한 조정 (거래량 감소)")
    elif vol_ratio < 1.0:
        score += 20
        reasons.append("양호한 조정 (거래량 유지)")
    elif vol_ratio < 1.5:
        score += 10
        reasons.append("보통 조정 (거래량 증가)")
    else:
        reasons.append("불안한 조정 (거래량 급증)")
    
    # RSI
    if rsi > 70:
        score += 30
        reasons.append("강한 추세 (RSI > 70)")
    elif rsi > 65:
        score += 25
        reasons.append("양호한 추세 (RSI > 65)")
    elif rsi > 60:
        score += 15
        reasons.append("보통 추세 (RSI > 60)")
    else:
        reasons.append("약한 추세 (RSI <= 60)")
    
    if score >= 80: confidence = "high"
    elif score >= 60: confidence = "medium"
    else: confidence = "low"
    
    return {
        "score": score,
        "confidence": confidence,
        "max_score": 100,
        "reasons": reasons,
        "retracement_pct": retracement_pct,
        "vol_ratio": vol_ratio,
        "rsi": rsi
    }
