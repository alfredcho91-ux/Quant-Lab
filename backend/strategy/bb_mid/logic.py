"""BB Mid Touch 통계 계산 로직"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from core.indicators import add_bb_indicators as _core_add_bb_indicators


def add_bb_indicators(
    df: pd.DataFrame,
    bb_length: int = 20,
    bb_std_mult: float = 2.0,
    rsi_length: int = 14,
    sma200_length: int = 200,
) -> pd.DataFrame:
    """
    볼린저 밴드, RSI, SMA200 지표 추가
    
    Args:
        df: OHLCV 데이터프레임
        bb_length: 볼린저 밴드 기간
        bb_std_mult: 볼린저 밴드 표준편차 배수
        rsi_length: RSI 기간
        sma200_length: SMA200 기간
    
    Returns:
        지표가 추가된 데이터프레임
    """
    # Delegate to the single canonical implementation in core.indicators.
    return _core_add_bb_indicators(
        df=df,
        bb_length=bb_length,
        bb_std_mult=bb_std_mult,
        rsi_length=rsi_length,
        sma200_length=sma200_length,
    )


def _build_event_filter(
    df: pd.DataFrame,
    start_side: str,
    regime: Optional[str] = None,
) -> pd.Series:
    """
    BB 이벤트 필터 조건 생성
    
    Args:
        df: BB 지표가 포함된 DataFrame
        start_side: "lower" 또는 "upper"
        regime: "above_sma200", "below_sma200", 또는 None
    
    Returns:
        필터 조건 Series (boolean)
    """
    if start_side == "lower":
        cond = df["touch_lower"]
    else:
        cond = df["touch_upper"]
    
    if regime == "above_sma200":
        cond = cond & (df["close"] > df["SMA200"])
    elif regime == "below_sma200":
        cond = cond & (df["close"] < df["SMA200"])
    
    return cond


def analyze_bb_mid_touch(
    df: pd.DataFrame,
    start_side: str,
    max_bars: int,
    regime: Optional[str],
) -> Dict:
    """
    BB 중단 터치 통계 분석
    
    Args:
        df: BB 지표가 포함된 DataFrame
        start_side: "lower" 또는 "upper"
        max_bars: 최대 분석 기간
        regime: "above_sma200", "below_sma200", 또는 None
    
    Returns:
        통계 결과 딕셔너리
        - failed_in_n: n봉 이내 터치 실패한 이벤트 수 (이후 5봉 검사 가능한 것만)
        - next5_bar_counts: {1..5} 정확히 k봉째 터치한 이벤트 수
        - next5_bar_rates: {1..5} k봉째 터치 확률 (%)
    """
    # Filter events
    cond = _build_event_filter(df, start_side, regime)
    
    # 연속 터치 중 최초 봉만 선택 (연속 터치 제외)
    touch_series = cond.astype(int)
    first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
    
    event_idx = df.index[first_touch]
    if len(event_idx) == 0:
        return {
            "events": 0,
            "success": 0,
            "success_rate": None,
            "failed_in_n": 0,
            "next5_bar_counts": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "next5_bar_rates": {1: None, 2: None, 3: None, 4: None, 5: None},
        }
    
    pos_idx = df.index.get_indexer(event_idx)
    touch_mid = df["touch_mid"].values
    max_i = len(df) - 1
    extend_bars = 5
    
    total, success = 0, 0
    failed_in_n = 0
    bar_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for i in pos_idx:
        start, end = i + 1, i + max_bars
        if start > max_i:
            continue
        end = min(end, max_i)
        if start > end:
            continue
        total += 1
        touched = np.any(touch_mid[start : end + 1])
        if touched:
            success += 1
        else:
            end_full = i + max_bars
            if end_full + extend_bars <= max_i:
                failed_in_n += 1
                # 정확히 k봉째에 최초 터치한지 판정 (1~5)
                found = False
                for k in range(1, 6):
                    bk = end_full + k
                    if touch_mid[bk]:
                        bar_counts[k] += 1
                        found = True
                        break
                    # k봉째 미터치 → 다음 봉 검사
    
    success_rate = success / total * 100.0 if total > 0 else None
    bar_rates = {}
    for k in range(1, 6):
        bar_rates[k] = bar_counts[k] / failed_in_n * 100.0 if failed_in_n > 0 else None
    
    return {
        "events": total,
        "success": success,
        "success_rate": success_rate,
        "failed_in_n": failed_in_n,
        "next5_bar_counts": bar_counts,
        "next5_bar_rates": bar_rates,
    }


def collect_event_returns(
    df: pd.DataFrame,
    start_side: str,
    max_bars: int,
    regime: Optional[str],
) -> Dict:
    """
    이벤트별 MFE, MAE, End Return 수집
    
    Args:
        df: BB 지표가 포함된 DataFrame
        start_side: "lower" 또는 "upper"
        max_bars: 최대 분석 기간
        regime: "above_sma200", "below_sma200", 또는 None
    
    Returns:
        MFE, MAE, End Return 리스트
    """
    # Filter events
    cond = _build_event_filter(df, start_side, regime)
    
    # 연속 터치 중 최초 봉만 선택 (연속 터치 제외)
    touch_series = cond.astype(int)
    first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
    
    event_idx = df.index[first_touch]
    if len(event_idx) == 0:
        return {"mfe": [], "mae": [], "end": []}
    
    pos_idx = df.index.get_indexer(event_idx)
    highs, lows, closes = df["high"].values, df["low"].values, df["close"].values
    max_i = len(df) - 1
    
    mfe_list, mae_list, end_list = [], [], []
    for i in pos_idx:
        start, end = i + 1, i + max_bars
        if start > max_i:
            continue
        end = min(end, max_i)
        if start > end:
            continue
        
        P0 = closes[i]
        if not np.isfinite(P0) or P0 <= 0:
            continue
        
        seg_high = highs[start:end + 1]
        seg_low = lows[start:end + 1]
        seg_close = closes[end]
        
        mfe_pct = float(np.nanmax((seg_high - P0) / P0 * 100.0))
        mae_pct = float(np.nanmin((seg_low - P0) / P0 * 100.0))
        end_pct = float((seg_close - P0) / P0 * 100.0)
        
        if np.isfinite(mfe_pct):
            mfe_list.append(mfe_pct)
        if np.isfinite(mae_pct):
            mae_list.append(mae_pct)
        if np.isfinite(end_pct):
            end_list.append(end_pct)
    
    return {"mfe": mfe_list, "mae": mae_list, "end": end_list}


def quartile_reach_stats(
    df: pd.DataFrame,
    start_side: str,
    max_bars: int,
    regime: Optional[str],
) -> Dict:
    """
    밴드 4분위 최대 도달 분포 계산
    
    Args:
        df: BB 지표가 포함된 DataFrame
        start_side: "lower" 또는 "upper"
        max_bars: 최대 분석 기간
        regime: "above_sma200", "below_sma200", 또는 None
    
    Returns:
        분위별 분포 딕셔너리
    """
    # Filter events
    cond = _build_event_filter(df, start_side, regime)
    
    # 연속 터치 중 최초 봉만 선택 (연속 터치 제외)
    touch_series = cond.astype(int)
    first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
    
    event_idx = df.index[first_touch]
    pos_idx = df.index.get_indexer(event_idx)
    
    if len(pos_idx) == 0:
        return {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "Total": 0}
    
    highs = df["high"].values
    lows = df["low"].values
    lower = df["BB_lower"].values
    upper = df["BB_upper"].values
    
    width = upper - lower
    width_safe = np.where(width <= 0, np.nan, width)
    max_i = len(df) - 1
    
    c_q1, c_q2, c_q3, c_q4, total = 0, 0, 0, 0, 0
    
    for i in pos_idx:
        start, end = i + 1, i + max_bars
        if start > max_i:
            continue
        end = min(end, max_i)
        if start > end:
            continue
        
        seg_width = width_safe[start:end + 1]
        valid = np.isfinite(seg_width) & (seg_width > 0)
        if not np.any(valid):
            continue
        
        seg_lower = lower[start:end + 1][valid]
        seg_width_valid = seg_width[valid]
        
        if start_side == "lower":
            # Lower touch: check how high (based on high) → 0=lower, 1=upper
            seg_high = highs[start:end + 1][valid]
            pos = (seg_high - seg_lower) / seg_width_valid
            pos = np.clip(pos, 0.0, 1.0)
            metric = float(np.nanmax(pos))  # Maximum upward position
        else:
            # Upper touch: check how low (based on low) → 0=lower, 1=upper
            seg_low = lows[start:end + 1][valid]
            pos = (seg_low - seg_lower) / seg_width_valid
            pos = np.clip(pos, 0.0, 1.0)
            metric = float(np.nanmin(pos))  # Minimum downward position
        
        if not np.isfinite(metric):
            continue
        
        total += 1
        
        # Quartile classification (0=lower band, 1=upper band)
        if metric <= 0.25:
            c_q1 += 1
        elif metric <= 0.50:
            c_q2 += 1
        elif metric <= 0.75:
            c_q3 += 1
        else:
            c_q4 += 1
    
    return {"Q1": c_q1, "Q2": c_q2, "Q3": c_q3, "Q4": c_q4, "Total": total}
