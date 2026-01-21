"""
주간 패턴 분석 기술적 지표 계산 모듈
RSI, NATR 등 기술적 지표 계산 로직 분리
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# 상수
DEFAULT_RSI_PERIOD = 14
DEFAULT_ATR_PERIOD = 14
DEFAULT_VOL_PERIOD = 20


# ========== 설정 클래스 ==========

@dataclass
class IndicatorConfig:
    """기술적 지표 설정"""
    rsi_period: int = DEFAULT_RSI_PERIOD
    atr_period: int = DEFAULT_ATR_PERIOD
    vol_period: int = DEFAULT_VOL_PERIOD
    
    def __post_init__(self):
        """유효성 검증"""
        if self.rsi_period < 1:
            raise ValueError(f"RSI 기간은 1 이상이어야 합니다: {self.rsi_period}")
        if self.atr_period < 1:
            raise ValueError(f"ATR 기간은 1 이상이어야 합니다: {self.atr_period}")
        if self.vol_period < 1:
            raise ValueError(f"거래량 이동평균 기간은 1 이상이어야 합니다: {self.vol_period}")


# ========== 기술적 지표 계산 함수 ==========

def compute_rsi(close: pd.Series, length: int = DEFAULT_RSI_PERIOD, min_periods: Optional[int] = None) -> pd.Series:
    """
    RSI 계산 (Look-ahead Bias 방지: min_periods 명시)
    
    Args:
        close: 종가 시리즈
        length: RSI 기간
        min_periods: 최소 기간 (None이면 length와 동일)
    """
    if min_periods is None:
        min_periods = length
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length, min_periods=min_periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length, min_periods=min_periods).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_natr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = DEFAULT_ATR_PERIOD, min_periods: Optional[int] = None) -> pd.Series:
    """
    Normalized ATR (NATR) 계산: ATR / Close * 100
    
    Args:
        high: 고가 시리즈
        low: 저가 시리즈
        close: 종가 시리즈
        length: ATR 기간
        min_periods: 최소 기간 (None이면 length와 동일)
    """
    if min_periods is None:
        min_periods = length
    
    # True Range 계산
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR 계산
    atr = tr.rolling(window=length, min_periods=min_periods).mean()
    
    # NATR 계산 (정규화)
    natr = (atr / close) * 100
    
    return natr


def calculate_technical_indicators(df: pd.DataFrame, config: IndicatorConfig) -> pd.DataFrame:
    """
    기술적 지표 계산 및 DataFrame에 추가
    
    Args:
        df: 일봉 DataFrame
        config: 지표 설정
    
    Returns:
        지표가 추가된 DataFrame
    """
    df = df.copy()
    
    # RSI 계산
    if 'close' in df.columns:
        df['rsi'] = compute_rsi(df['close'], length=config.rsi_period)
    
    # NATR 계산
    if all(col in df.columns for col in ['high', 'low', 'close']):
        df['natr'] = compute_natr(
            df['high'], 
            df['low'], 
            df['close'], 
            length=config.atr_period
        )
    
    # 거래량 이동평균 및 상대 거래량
    if 'volume' in df.columns:
        df['vol_ma'] = df['volume'].rolling(window=config.vol_period, min_periods=config.vol_period).mean()
        # 상대 거래량 (현재 거래량 / 이동평균 거래량)
        df['rel_vol'] = df['volume'] / df['vol_ma']
    
    return df
