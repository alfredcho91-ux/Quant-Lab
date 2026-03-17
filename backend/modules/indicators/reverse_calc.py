import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

def calculate_required_price_for_rsi(closes: pd.Series, target_rsi: float = 30.0, period: int = 14) -> Optional[float]:
    """
    목표 RSI 값에 도달하기 위해 필요한 다음 캔들의 종가(Close)를 역산합니다.
    Wilder's Smoothing (RMA) 방식을 사용합니다.
    """
    if len(closes) < period + 1:
        return None
        
    # 1. 기존 데이터로 Gain/Loss 계산
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # 2. 현재 시점의 평균 Gain/Loss (Wilder's Smoothing)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean().iloc[-1]
    
    # 3. 목표 RS 계산
    if target_rsi >= 100:
        return float('inf')
    if target_rsi <= 0:
        return 0.0
        
    target_rs = target_rsi / (100.0 - target_rsi)
    
    # 4. 다음 캔들의 필요 Gain/Loss 역산
    # 공식: target_rs = (avg_gain * (period - 1) + next_gain) / (avg_loss * (period - 1) + next_loss)
    # next_gain과 next_loss는 둘 중 하나만 0보다 큼.
    
    current_close = closes.iloc[-1]
    
    # Case A: 가격이 올라서(next_gain > 0, next_loss = 0) 목표 RSI 도달
    required_gain = target_rs * (avg_loss * (period - 1)) - (avg_gain * (period - 1))
    if required_gain >= 0:
        return float(current_close + required_gain)
        
    # Case B: 가격이 떨어져서(next_gain = 0, next_loss > 0) 목표 RSI 도달
    required_loss = ((avg_gain * (period - 1)) / target_rs) - (avg_loss * (period - 1))
    if required_loss >= 0:
        return float(current_close - required_loss)
        
    return current_close

def calculate_required_price_for_stoch(highs: pd.Series, lows: pd.Series, closes: pd.Series, target_k: float = 20.0, k_window: int = 5) -> Optional[float]:
    """
    목표 Stochastic %K 값에 도달하기 위해 필요한 다음 캔들의 종가(Close)를 역산합니다.
    """
    if len(closes) < k_window:
        return None
        
    # 최근 (k_window - 1)개의 High, Low (다음 캔들이 추가될 것이므로 1개 뺌)
    recent_highs = highs.iloc[-(k_window - 1):]
    recent_lows = lows.iloc[-(k_window - 1):]
    
    hh = recent_highs.max()
    ll = recent_lows.min()
    
    # 공식: %K = (Close - LL) / (HH - LL) * 100
    # Close = (%K / 100) * (HH - LL) + LL
    
    # 가정 1: 다음 종가가 기존 HH, LL 범위를 벗어나지 않을 때
    target_ratio = target_k / 100.0
    projected_close = target_ratio * (hh - ll) + ll
    
    # 가정 2: 다음 종가가 새로운 LL을 갱신할 때 (하락 돌파)
    # Close = LL_new 이고, %K = 0이 됨. target_k가 0이 아니면 모순.
    if target_k == 0:
        return float(ll) # LL 이하 아무 가격이나 됨
        
    # 가정 3: 다음 종가가 새로운 HH를 갱신할 때 (상승 돌파)
    # Close = HH_new 이고, %K = 100이 됨. target_k가 100이 아니면 모순.
    if target_k == 100:
        return float(hh) # HH 이상 아무 가격이나 됨
        
    return float(projected_close)

def get_indicator_projections(df: pd.DataFrame) -> Dict[str, Any]:
    """
    데이터프레임을 받아 주요 지표들의 도달 예상 가격을 반환합니다.
    """
    if df.empty or len(df) < 20:
        return {"error": "Not enough data"}
        
    closes = df['close'] # type: ignore
    highs = df['high'] # type: ignore
    lows = df['low'] # type: ignore
    current_price = float(closes.iloc[-1])
    
    k_window = 5
    stoch_hh = None
    stoch_ll = None
    
    if len(closes) >= k_window:
        recent_highs = highs.iloc[-(k_window - 1):]
        recent_lows = lows.iloc[-(k_window - 1):]
        stoch_hh = float(recent_highs.max())
        stoch_ll = float(recent_lows.min())

    # Calculate raw projections
    projections = {
        "rsi_30": calculate_required_price_for_rsi(closes, target_rsi=30.0), # type: ignore
        "rsi_70": calculate_required_price_for_rsi(closes, target_rsi=70.0), # type: ignore
        "stoch_20": calculate_required_price_for_stoch(highs, lows, closes, target_k=20.0), # type: ignore
        "stoch_80": calculate_required_price_for_stoch(highs, lows, closes, target_k=80.0), # type: ignore
        "stoch_hh": stoch_hh,
        "stoch_ll": stoch_ll,
    }

    # Sanitize NaN values to None for valid JSON
    sanitized_projections = {
        k: (None if isinstance(v, float) and np.isnan(v) else v)
        for k, v in projections.items()
    }

    return {
        "current_price": current_price,
        "projections": sanitized_projections
    }
