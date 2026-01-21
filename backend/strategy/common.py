"""
전략 관련 공통 통계 함수 및 유틸리티

Note:
    - 핵심 공통 기능 (AnalysisContext, DataCache, load_data 등)은 strategy.streak.common에 정의
    - 이 모듈은 통계 계산 함수를 제공하며, 다른 전략에서 공유 가능
    - weekly_pattern, backtest_logic 등에서 사용
"""

import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from typing import Dict, Any, Optional, Tuple, List

# streak.common에서 핵심 기능 import (중복 제거)
from strategy.streak.common import (
    # 상수
    DEFAULT_RSI,
    RSI_THRESHOLD_DEFAULT,
    RSI_OVERBOUGHT,
    MAX_RETRACEMENT_DEFAULT,
    CONFIDENCE_LEVEL,
    MIN_SAMPLE_SIZE_RELIABLE,
    MIN_SAMPLE_SIZE_MEDIUM,
    DISP_BINS,
    RSI_BINS,
    # 유틸리티 함수
    safe_float,
    safe_round,
    sanitize_for_json,
    # Context 및 캐시
    AnalysisContext,
    DataCache,
    data_cache,
    analysis_cache,
    # 데이터 함수
    load_data,
    prepare_dataframe,
    normalize_indices,
    extract_c1_indices,
    normalize_datetime_index,
    get_cache_stats,
    clear_cache,
    generate_analysis_cache_key,
    # 통계 함수 (streak/common에서 이미 정의된 것)
    bonferroni_correction,
    calculate_binomial_pvalue,
    safe_get_rsi,
    analyze_interval_statistics,
    find_complex_pattern,
    # 분석 함수
    analyze_pullback_quality,
    calculate_signal_score,
    calculate_intraday_distribution,
    # 통계 함수 (streak/statistics.py에서 re-export)
    wilson_confidence_interval,
    trimmed_stats,
)


# ========== 통계 함수 (이 모듈의 고유 함수) ==========
# wilson_confidence_interval, trimmed_stats는 strategy.streak.statistics에서 import

def calculate_sharpe_ratio_unified(
    returns: pd.Series,
    period: str = 'daily',
    risk_free_rate: float = 0.0
) -> Optional[float]:
    """
    Sharpe Ratio 계산 (통합 버전)
    
    Args:
        returns: 수익률 시리즈
        period: 데이터 주기 ('daily', 'weekly', 'monthly')
        risk_free_rate: 무위험 수익률 (기본값 0)
    
    Returns:
        Sharpe Ratio 또는 None
    """
    if len(returns) == 0:
        return None
    
    excess_returns = returns - risk_free_rate
    if excess_returns.std() == 0:
        return None
    
    annualization_factors = {
        'daily': np.sqrt(252),
        'weekly': np.sqrt(52),
        'monthly': np.sqrt(12),
    }
    
    factor = annualization_factors.get(period, np.sqrt(252))
    sharpe = excess_returns.mean() / excess_returns.std() * factor
    
    return safe_float(sharpe)


def calculate_max_drawdown_unified(
    returns: pd.Series,
    method: str = 'cumprod'
) -> Dict[str, Any]:
    """
    Maximum Drawdown (MDD) 계산 (통합 버전)
    
    Args:
        returns: 수익률 시리즈 (cumprod) 또는 PnL 시리즈 (cumsum)
        method: 계산 방식 ('cumprod' 또는 'cumsum')
    
    Returns:
        {"max_drawdown": float, "max_drawdown_pct": float}
    """
    if len(returns) == 0:
        return {"max_drawdown": None, "max_drawdown_pct": None}
    
    if method == 'cumprod':
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        max_dd_pct = safe_float(max_dd * 100) if max_dd is not None else None
    else:
        cumulative = returns.cumsum()
        peak = np.maximum.accumulate(cumulative)
        drawdown = peak - cumulative
        max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0
        max_dd_pct = float(max_dd / (np.max(peak) + 1e-10) * 100) if np.max(peak) > 0 else 0
    
    return {
        "max_drawdown": safe_float(max_dd),
        "max_drawdown_pct": max_dd_pct
    }


def calculate_t_test_unified(returns: pd.Series) -> Dict[str, Any]:
    """
    t-test: 평균 수익률이 0과 유의미하게 다른지 검증
    
    Args:
        returns: 수익률 시리즈
    
    Returns:
        {"t_statistic": float, "p_value": float, "is_significant": bool}
    """
    if len(returns) < 2:
        return {"t_statistic": None, "p_value": None, "is_significant": False}
    
    t_stat, p_value = scipy_stats.ttest_1samp(returns, 0.0)
    
    return {
        "t_statistic": safe_float(t_stat),
        "p_value": safe_float(p_value),
        "is_significant": p_value < 0.05 if p_value else False
    }


def calculate_profit_factor(returns: pd.Series) -> Optional[float]:
    """
    Profit Factor 계산
    
    Args:
        returns: 수익률 또는 PnL 시리즈
    
    Returns:
        Profit Factor 또는 None
    """
    if len(returns) == 0:
        return None
    
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    
    if gross_loss == 0:
        return None
    
    pf = gross_profit / gross_loss
    return safe_float(pf) if not np.isinf(pf) and not np.isnan(pf) else None


def calculate_max_consecutive_loss(returns: pd.Series) -> int:
    """
    최대 연속 손실 횟수 계산
    
    Args:
        returns: 수익률 또는 PnL 시리즈
    
    Returns:
        최대 연속 손실 횟수
    """
    if len(returns) == 0:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for ret in returns:
        if ret < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive


def calculate_returns_confidence_interval(
    returns: pd.Series,
    confidence: float = 0.95
) -> Dict[str, Any]:
    """
    수익률 신뢰구간 계산 (t-distribution 사용)
    
    Args:
        returns: 수익률 시리즈
        confidence: 신뢰수준 (기본값 0.95)
    
    Returns:
        {"ci_lower": float, "ci_upper": float, "ci_width": float}
    """
    if len(returns) == 0:
        return {"ci_lower": None, "ci_upper": None, "ci_width": None}
    
    mean = returns.mean()
    std = returns.std()
    n = len(returns)
    
    if n < 2 or std == 0:
        return {
            "ci_lower": safe_float(mean * 100),
            "ci_upper": safe_float(mean * 100),
            "ci_width": 0.0
        }
    
    t_value = scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n-1)
    margin = t_value * std / np.sqrt(n)
    
    ci_lower = (mean - margin) * 100
    ci_upper = (mean + margin) * 100
    
    return {
        "ci_lower": safe_float(ci_lower),
        "ci_upper": safe_float(ci_upper),
        "ci_width": safe_float(ci_upper - ci_lower)
    }


# ========== 하위 호환성을 위한 re-export ==========
__all__ = [
    # 상수
    'DEFAULT_RSI',
    'RSI_THRESHOLD_DEFAULT',
    'RSI_OVERBOUGHT',
    'MAX_RETRACEMENT_DEFAULT',
    'CONFIDENCE_LEVEL',
    'MIN_SAMPLE_SIZE_RELIABLE',
    'MIN_SAMPLE_SIZE_MEDIUM',
    'DISP_BINS',
    'RSI_BINS',
    # 유틸리티
    'safe_float',
    'safe_round',
    'sanitize_for_json',
    # Context/Cache
    'AnalysisContext',
    'DataCache',
    'data_cache',
    'analysis_cache',
    # 데이터 함수
    'load_data',
    'prepare_dataframe',
    'normalize_indices',
    'extract_c1_indices',
    'normalize_datetime_index',
    'get_cache_stats',
    'clear_cache',
    'generate_analysis_cache_key',
    # 통계 함수
    'wilson_confidence_interval',
    'bonferroni_correction',
    'calculate_binomial_pvalue',
    'safe_get_rsi',
    'analyze_interval_statistics',
    'trimmed_stats',
    'calculate_sharpe_ratio_unified',
    'calculate_max_drawdown_unified',
    'calculate_t_test_unified',
    'calculate_profit_factor',
    'calculate_max_consecutive_loss',
    'calculate_returns_confidence_interval',
    # 패턴 분석
    'find_complex_pattern',
    'analyze_pullback_quality',
    'calculate_signal_score',
    'calculate_intraday_distribution',
]
