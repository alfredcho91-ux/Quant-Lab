"""Simple Mode 전략 (N-연속 양봉/음봉 분석)"""

import pandas as pd
from typing import Dict, Any, Optional
import logging
import traceback

from strategy.context import AnalysisContext
from strategy.streak.common import get_or_calculate_indicators, sanitize_for_json
from strategy.streak.data_ops import filter_rows_by_ema_200_position
from strategy.streak.simple_analyzer import calculate_simple_metrics
from strategy.streak.simple_runner import collect_simple_target_cases

logger = logging.getLogger(__name__)


def run_simple_analysis(df: pd.DataFrame, context: AnalysisContext, from_cache: bool = False) -> Dict[str, Any]:
    """
    Simple Mode 분석 실행
    
    Args:
        df: 준비된 DataFrame (prepare_dataframe으로 처리됨)
        context: 분석 컨텍스트
        from_cache: 캐시 사용 여부
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        n = context.n_streak

        target_cases = collect_simple_target_cases(
            df=df,
            n_streak=n,
            min_total_body_pct=context.min_total_body_pct,
        )
        if target_cases.empty:
            return _empty_simple_result(context, from_cache)

        df = get_or_calculate_indicators(context.coin, context.interval, df)
        total_matches = len(target_cases)
        target_cases = filter_rows_by_ema_200_position(
            df=df,
            rows=target_cases,
            ema_200_position=context.ema_200_position,
        )
        if target_cases.empty:
            return _empty_simple_result(
                context,
                from_cache,
                filter_status={
                    "status": "filtered_out",
                    "total_matches": total_matches,
                    "filtered_count": 0,
                    "ema_200_position": context.ema_200_position,
                },
            )

        metrics = calculate_simple_metrics(df=df, target_cases=target_cases, context=context)

        result = {
            "success": True,
            "mode": "simple",
            "filter_status": None,
            "complex_pattern_analysis": None,
            "ny_trading_guide": None,
            "analysis_mode": {
                "type": "simple",
                "description": "Simple N-Streak",
                "parameters": {
                    "n_streak": n,
                    "direction": context.direction,
                    "filters": {
                        "ema_200_position": context.ema_200_position,
                        "min_total_body_pct": context.min_total_body_pct,
                    },
                },
            },
            "from_cache": from_cache,
            "coin": context.coin,
            "interval": context.interval,
            "n_streak": n,
            "direction": context.direction,
            **metrics,
        }
        return sanitize_for_json(result)

    except Exception as e:
        logger.error(f"Error in run_simple_analysis: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "mode": "simple"
        }


def _empty_simple_result(
    context: AnalysisContext,
    from_cache: bool,
    filter_status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """빈 결과 반환 (패턴을 찾을 수 없을 때)"""
    return {
        "success": True,
        "mode": "simple",
        "filter_status": filter_status,
        "total_cases": 0,
        "continuation_rate": None,
        "reversal_rate": None,
        "avg_body_pct": None,
        "c2_after_c1_green_rate": None,
        "c2_after_c1_red_rate": None,
        "c1_green_count": 0,
        "c1_red_count": 0,
        "comparative_report": None,
        "volatility_stats": None,
        "rsi_by_interval": {},
        "disp_by_interval": {},
        "atr_by_interval": {},
        "rsi_atr_heatmap": None,
        "high_prob_rsi_intervals": {},
        "high_prob_disp_intervals": {},
        "high_prob_atr_intervals": {},
        "complex_pattern_analysis": None,
        "ny_trading_guide": None,
        "analysis_mode": {
            "type": "simple",
            "description": "Simple N-Streak",
            "parameters": {
                "n_streak": context.n_streak,
                "direction": context.direction,
                "filters": {
                    "ema_200_position": context.ema_200_position,
                    "min_total_body_pct": context.min_total_body_pct,
                },
            }
        },
        "from_cache": from_cache,
        "coin": context.coin,
        "interval": context.interval,
        "n_streak": context.n_streak,
        "direction": context.direction,
    }
