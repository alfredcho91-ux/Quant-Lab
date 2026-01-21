"""
주간 패턴 통계 계산 모듈

통계 계산 및 필터 적용 함수를 제공합니다.
"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

from strategy.streak.common import safe_float
from strategy.common import (
    calculate_sharpe_ratio_unified,
    calculate_max_drawdown_unified,
    calculate_t_test_unified,
    calculate_profit_factor,
    calculate_max_consecutive_loss,
    calculate_returns_confidence_interval,
)
from strategy.weekly_pattern.config import FilterConfig

logger = logging.getLogger(__name__)

# 상수
CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE_RELIABLE = 30
MIN_SAMPLE_SIZE_WARNING = 10


def calculate_stats_for_subset(subset: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    필터링된 데이터셋에 대한 통계 계산
    
    Args:
        subset: 분석할 DataFrame (ret_mid_late 컬럼 필요)
    
    Returns:
        통계 결과 딕셔너리 또는 None
    """
    if len(subset) == 0:
        return None
    
    ret_series = subset['ret_mid_late'].dropna()
    
    if len(ret_series) == 0:
        return None
    
    # 기본 통계
    wins = (ret_series > 0).sum()
    total = len(ret_series)
    wr = wins / total if total > 0 else 0.0
    ev = ret_series.mean()
    std = ret_series.std()
    
    # Profit Factor
    pf = calculate_profit_factor(ret_series)
    
    # t-test
    t_test = calculate_t_test_unified(ret_series)
    
    # 신뢰구간
    ci = calculate_returns_confidence_interval(ret_series, confidence=CONFIDENCE_LEVEL)
    
    # 최대 연속 손실
    max_consecutive_loss = calculate_max_consecutive_loss(ret_series)
    
    # Sharpe Ratio
    sharpe = calculate_sharpe_ratio_unified(ret_series, period='daily')
    
    # MDD
    mdd_result = calculate_max_drawdown_unified(ret_series, method='cumprod')
    
    # 양수/음수 합계
    pos_sum = ret_series[ret_series > 0].sum()
    neg_sum = abs(ret_series[ret_series < 0].sum())
    
    # 최대 연속 수익
    max_consecutive_win = 0
    current_win = 0
    for ret in ret_series:
        if ret > 0:
            current_win += 1
            max_consecutive_win = max(max_consecutive_win, current_win)
        else:
            current_win = 0
    
    return {
        "sample_count": total,
        "win_rate": safe_float(wr * 100),
        "expected_return": safe_float(ev * 100),
        "volatility": safe_float(std * 100),
        "profit_factor": pf,
        "positive_sum": safe_float(pos_sum * 100),
        "negative_sum": safe_float(neg_sum * 100),
        "sharpe_ratio": sharpe,
        "max_drawdown": mdd_result,
        "max_consecutive_loss": max_consecutive_loss,
        "max_consecutive_win": max_consecutive_win,
        "t_test": t_test,
        "confidence_interval": ci,
        "reliability": "high" if total >= MIN_SAMPLE_SIZE_RELIABLE else "medium" if total >= MIN_SAMPLE_SIZE_WARNING else "low"
    }


def apply_filters_and_calculate_stats(
    df_w: pd.DataFrame,
    filter_config: FilterConfig
) -> Dict[str, Any]:
    """
    필터 적용 및 통계 계산
    
    Args:
        df_w: 주간 패턴 DataFrame
        filter_config: 필터 설정 객체
    
    Returns:
        필터별 통계 결과 딕셔너리
    """
    results = {}
    
    if filter_config.direction == "down":
        # 하락 케이스 분석
        # [1] 전체 주 초반 하락 케이스 (Baseline)
        early_down = df_w[df_w['ret_early'] < 0]
        baseline_stats = calculate_stats_for_subset(early_down)
        if baseline_stats:
            baseline_stats['title'] = "BASE: Early Down (Mon-Tue < 0)"
            baseline_stats['description'] = "주 초반 하락 케이스 (기준선)"
            results['baseline'] = baseline_stats
        
        # [2] 깊은 하락 필터
        deep_drop = early_down[early_down['ret_early'] <= filter_config.deep_drop_threshold]
        deep_drop_stats = calculate_stats_for_subset(deep_drop)
        if deep_drop_stats:
            deep_drop_stats['title'] = f"FILTER: Deep Drop (Mon-Tue <= {filter_config.deep_drop_threshold*100:.1f}%)"
            deep_drop_stats['description'] = f"주 초반 {filter_config.deep_drop_threshold*100:.1f}% 이상 하락"
            results['deep_drop'] = deep_drop_stats
        
        # [3] 과매도 필터 (RSI < threshold)
        oversold = early_down[early_down['rsi_tue'] <= filter_config.rsi_threshold]
        oversold_stats = calculate_stats_for_subset(oversold)
        if oversold_stats:
            oversold_stats['title'] = f"FILTER: Oversold (RSI <= {filter_config.rsi_threshold})"
            oversold_stats['description'] = f"화요일 RSI {filter_config.rsi_threshold} 이하"
            results['oversold'] = oversold_stats
        
        # [4] 복합 필터 (깊은 하락 + 과매도)
        combined_filter = early_down[
            (early_down['ret_early'] <= filter_config.deep_drop_threshold) & 
            (early_down['rsi_tue'] <= filter_config.rsi_threshold)
        ]
        combined_stats = calculate_stats_for_subset(combined_filter)
        if combined_stats:
            combined_stats['title'] = f"FILTER: Deep Drop + Oversold"
            combined_stats['description'] = f"주 초반 {filter_config.deep_drop_threshold*100:.1f}% 이상 하락 + RSI {filter_config.rsi_threshold} 이하"
            results['combined'] = combined_stats
    
    else:  # direction == "up"
        # 상승 케이스 분석
        # [1] 전체 주 초반 상승 케이스 (Baseline)
        early_up = df_w[df_w['ret_early'] > 0]
        baseline_stats = calculate_stats_for_subset(early_up)
        if baseline_stats:
            baseline_stats['title'] = "BASE: Early Up (Mon-Tue > 0)"
            baseline_stats['description'] = "주 초반 상승 케이스 (기준선)"
            results['baseline'] = baseline_stats
        
        # [2] 깊은 상승 필터
        deep_rise = early_up[early_up['ret_early'] >= filter_config.deep_rise_threshold]
        deep_rise_stats = calculate_stats_for_subset(deep_rise)
        if deep_rise_stats:
            deep_rise_stats['title'] = f"FILTER: Deep Rise (Mon-Tue >= {filter_config.deep_rise_threshold*100:.1f}%)"
            deep_rise_stats['description'] = f"주 초반 {filter_config.deep_rise_threshold*100:.1f}% 이상 상승"
            results['deep_rise'] = deep_rise_stats
        
        # [3] 과매수 필터 (RSI > (100 - threshold))
        overbought_threshold = 100 - filter_config.rsi_threshold
        overbought = early_up[early_up['rsi_tue'] >= overbought_threshold]
        overbought_stats = calculate_stats_for_subset(overbought)
        if overbought_stats:
            overbought_stats['title'] = f"FILTER: Overbought (RSI >= {overbought_threshold})"
            overbought_stats['description'] = f"화요일 RSI {overbought_threshold} 이상"
            results['overbought'] = overbought_stats
        
        # [4] 복합 필터 (깊은 상승 + 과매수)
        combined_filter = early_up[
            (early_up['ret_early'] >= filter_config.deep_rise_threshold) & 
            (early_up['rsi_tue'] >= overbought_threshold)
        ]
        combined_stats = calculate_stats_for_subset(combined_filter)
        if combined_stats:
            combined_stats['title'] = f"FILTER: Deep Rise + Overbought"
            combined_stats['description'] = f"주 초반 {filter_config.deep_rise_threshold*100:.1f}% 이상 상승 + RSI {overbought_threshold} 이상"
            results['combined'] = combined_stats
    
    # None 값 제거
    results = {k: v for k, v in results.items() if v is not None}
    
    return results
