"""
하이브리드 전략 분석 로직

EMA, MACD, RSI, ADX 등을 조합한 전략 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

from core.indicators import compute_live_indicators

logger = logging.getLogger(__name__)

# compute_refined_indicators는 compute_live_indicators로 통합됨
# 하위 호환성을 위한 alias
compute_refined_indicators = compute_live_indicators


def _prepare_indicators_and_signals(
    df: pd.DataFrame,
    strategies: Optional[List[str]] = None
) -> tuple[pd.DataFrame, Dict[str, pd.Series], List[str]]:
    """
    지표 계산 및 시그널 생성 공통 로직
    
    Args:
        df: OHLCV DataFrame
        strategies: 분석할 전략 리스트 (None이면 전체)
    
    Returns:
        (df_with_indicators, signals, selected_strategies) 튜플
    """
    # 지표 계산
    df_with_indicators = compute_live_indicators(df)
    df_with_indicators = df_with_indicators.dropna()
    
    if len(df_with_indicators) == 0:
        return None, {}, []
    
    # 시그널 생성
    signals = generate_strategy_signals(df_with_indicators)
    
    # 분석할 전략 선택
    if strategies is None:
        selected_strategies = list(signals.keys())
    else:
        selected_strategies = [s for s in strategies if s in signals]
    
    return df_with_indicators, signals, selected_strategies


def generate_strategy_signals(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    여러 전략 시그널 생성
    
    Args:
        df: 지표가 포함된 DataFrame
    
    Returns:
        전략별 시그널 딕셔너리
    """
    signals = {}
    
    # EMA_ADX_Strong: EMA20 > EMA50 & ADX > 25
    signals['EMA_ADX_Strong'] = (df['ema20'] > df['ema50']) & (df['adx'] > 25)
    
    # MACD_RSI_Trend: MACD > 0 & RSI > 55 & Close > SMA200
    signals['MACD_RSI_Trend'] = (
        (df['macd_hist'] > 0) & 
        (df['rsi'] > 55) & 
        (df['close'] > df['sma200'])
    )
    
    # Pure_Trend: Close > SMA200
    signals['Pure_Trend'] = (df['close'] > df['sma200'])
    
    return signals


def analyze_hybrid_strategy(
    df: pd.DataFrame,
    coin: str,
    interval: str,
    strategies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    하이브리드 전략 분석
    
    Args:
        df: OHLCV DataFrame
        coin: 코인 심볼
        interval: 시간프레임
        strategies: 분석할 전략 리스트 (None이면 전체)
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        # 지표 계산 및 시그널 생성
        df_with_indicators, signals, selected_strategies = _prepare_indicators_and_signals(df, strategies)
        
        if df_with_indicators is None or len(df_with_indicators) == 0:
            return {
                "success": False,
                "error": "지표 계산 후 유효한 데이터가 없습니다"
            }
        
        results = []
        for strategy_name in selected_strategies:
            signal = signals[strategy_name]
            signal_count = signal.sum()
            
            if signal_count == 0:
                continue
            
            # 시그널 발생 시점의 통계
            signal_data = df_with_indicators[signal]
            
            results.append({
                "strategy": strategy_name,
                "signal_count": int(signal_count),
                "signal_rate": float((signal_count / len(df_with_indicators)) * 100),
                "avg_rsi": float(signal_data['rsi'].mean()) if 'rsi' in signal_data.columns else None,
                "avg_adx": float(signal_data['adx'].mean()) if 'adx' in signal_data.columns else None,
            })
        
        return {
            "success": True,
            "coin": coin,
            "interval": interval,
            "total_candles": len(df_with_indicators),
            "strategies": results,
        }
        
    except Exception as e:
        logger.error(f"하이브리드 전략 분석 중 오류: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def analyze_live_mode(
    df: pd.DataFrame,
    coin: str,
    interval: str,
    strategies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    하이브리드 전략 라이브 모드 분석
    
    현재 시점(가장 최근 봉)에서 각 전략의 시그널 상태를 확인합니다.
    
    Args:
        df: OHLCV DataFrame
        coin: 코인 심볼
        interval: 시간프레임
        strategies: 분석할 전략 리스트 (None이면 전체)
    
    Returns:
        라이브 모드 분석 결과 딕셔너리
    """
    try:
        # 지표 계산 및 시그널 생성
        df_with_indicators, signals, selected_strategies = _prepare_indicators_and_signals(df, strategies)
        
        if df_with_indicators is None or len(df_with_indicators) == 0:
            return {
                "success": False,
                "error": "지표 계산 후 유효한 데이터가 없습니다"
            }
        
        # 완성된 전 봉 기준으로 계산 (진행 중인 봉이 아닌)
        if len(df_with_indicators) < 2:
            return {
                "success": False,
                "error": "완성된 봉이 부족합니다 (최소 2개 필요)"
            }
        
        # 전 봉(완성된 봉)의 데이터 사용
        latest = df_with_indicators.iloc[-2]  # -2: 전 봉 (완성된 봉)
        latest_timestamp = df_with_indicators.index[-2]  # 전 봉의 타임스탬프
        
        results = []
        for strategy_name in selected_strategies:
            signal = signals[strategy_name]
            # 전 봉의 시그널 상태 확인
            is_active = bool(signal.iloc[-2]) if len(signal) >= 2 else False
            
            # 현재 시그널 상태에 따른 상세 정보
            strategy_info = {
                "strategy": strategy_name,
                "is_active": is_active,
                "timestamp": latest_timestamp.isoformat() if hasattr(latest_timestamp, 'isoformat') else str(latest_timestamp),
            }
            
            # 각 전략별 조건 상세 정보
            if strategy_name == 'EMA_ADX_Strong':
                strategy_info.update({
                    "conditions": {
                        "ema20": float(latest['ema20']) if not pd.isna(latest['ema20']) else None,
                        "ema50": float(latest['ema50']) if not pd.isna(latest['ema50']) else None,
                        "adx": float(latest['adx']) if not pd.isna(latest['adx']) else None,
                        "ema20_above_ema50": bool(latest['ema20'] > latest['ema50']) if not pd.isna(latest['ema20']) and not pd.isna(latest['ema50']) else None,
                        "adx_above_25": bool(latest['adx'] > 25) if not pd.isna(latest['adx']) else None,
                    }
                })
            elif strategy_name == 'MACD_RSI_Trend':
                strategy_info.update({
                    "conditions": {
                        "macd_hist": float(latest['macd_hist']) if not pd.isna(latest['macd_hist']) else None,
                        "rsi": float(latest['rsi']) if not pd.isna(latest['rsi']) else None,
                        "close": float(latest['close']) if not pd.isna(latest['close']) else None,
                        "sma200": float(latest['sma200']) if not pd.isna(latest['sma200']) else None,
                        "macd_positive": bool(latest['macd_hist'] > 0) if not pd.isna(latest['macd_hist']) else None,
                        "rsi_above_55": bool(latest['rsi'] > 55) if not pd.isna(latest['rsi']) else None,
                        "close_above_sma200": bool(latest['close'] > latest['sma200']) if not pd.isna(latest['close']) and not pd.isna(latest['sma200']) else None,
                    }
                })
            elif strategy_name == 'Pure_Trend':
                strategy_info.update({
                    "conditions": {
                        "close": float(latest['close']) if not pd.isna(latest['close']) else None,
                        "sma200": float(latest['sma200']) if not pd.isna(latest['sma200']) else None,
                        "close_above_sma200": bool(latest['close'] > latest['sma200']) if not pd.isna(latest['close']) and not pd.isna(latest['sma200']) else None,
                    }
                })
            
            results.append(strategy_info)
        
        return {
            "success": True,
            "coin": coin,
            "interval": interval,
            "timestamp": latest_timestamp.isoformat() if hasattr(latest_timestamp, 'isoformat') else str(latest_timestamp),
            "current_price": float(latest['close']) if not pd.isna(latest['close']) else None,
            "strategies": results,
        }
        
    except Exception as e:
        logger.error(f"하이브리드 전략 라이브 모드 분석 중 오류: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
