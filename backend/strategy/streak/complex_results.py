"""Response builders for complex streak analysis mode."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from strategy.context import AnalysisContext
from strategy.streak.common import safe_round


def build_empty_complex_result(context: AnalysisContext, from_cache: bool) -> Dict[str, Any]:
    return {
        "success": False,
        "error": "복합 패턴이 비어있습니다",
        "message": "1차/2차 조건을 모두 설정해주세요",
        "mode": "complex",
        "from_cache": from_cache,
    }


def build_no_match_complex_result(
    context: AnalysisContext,
    complex_pattern: List[int],
    from_cache: bool,
) -> Dict[str, Any]:
    return {
        "success": False,
        "error": "패턴 매칭 실패",
        "message": f"{complex_pattern} 패턴을 찾을 수 없습니다",
        "suggestions": [
            "패턴을 단순화해보세요",
            "다른 타임프레임을 시도해보세요",
        ],
        "mode": "complex",
        "pattern": complex_pattern,
        "from_cache": from_cache,
    }


def build_quality_failure_result(
    *,
    total_matches: int,
    complex_pattern: List[int],
    from_cache: bool,
) -> Dict[str, Any]:
    return {
        "success": False,
        "error": "조정 품질 분석 실패",
        "message": "패턴은 매칭되었지만 분석 가능한 데이터가 없습니다",
        "total_matches": total_matches,
        "mode": "complex",
        "pattern": complex_pattern,
        "from_cache": from_cache,
    }


def build_filtered_out_complex_result(
    context: AnalysisContext,
    complex_pattern: List[int],
    from_cache: bool,
    total_matches: int,
) -> Dict[str, Any]:
    return {
        "success": True,
        "mode": "complex",
        "filter_status": {
            "status": "filtered_out",
            "total_matches": total_matches,
            "filtered_count": 0,
            "ema_200_position": context.ema_200_position,
        },
        "total_cases": 0,
        "continuation_rate": None,
        "reversal_rate": None,
        "continuation_count": 0,
        "reversal_count": 0,
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
            "type": "complex",
            "description": "Complex Pattern with Pullback",
            "parameters": {
                "complex_pattern": complex_pattern,
                "filters": {
                    "rsi_threshold": context.rsi_threshold,
                    "ema_200_position": context.ema_200_position,
                },
            },
        },
        "from_cache": from_cache,
        "coin": context.coin,
        "interval": context.interval,
        "n_streak": None,
        "direction": context.direction,
    }


def build_complex_filter_status(
    *,
    total_matches: int,
    quality_result_count: int,
    filtered_count: int,
    ema_200_position: Optional[str],
) -> Dict[str, Any]:
    filter_status = {
        "status": "success" if filtered_count > 0 else "filtered_out",
        "total_matches": total_matches,
        "quality_results": quality_result_count,
        "filtered_count": filtered_count,
        "ema_200_position": ema_200_position,
    }
    if filtered_count == 0:
        filter_status["message"] = f"{total_matches}개 패턴이 매칭되었지만 분석 가능한 케이스가 없습니다"
        filter_status["suggestions"] = ["다른 패턴을 시도해보세요"]
    return filter_status


def build_complex_success_result(
    *,
    context: AnalysisContext,
    complex_pattern: List[int],
    from_cache: bool,
    total_cases: int,
    filter_status: Dict[str, Any],
    complex_pattern_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    c1_analysis = complex_pattern_analysis.get("summary", {}).get("c1_analysis", {})
    c2_analysis = complex_pattern_analysis.get("summary", {}).get("c2_analysis", {})

    return {
        "success": True,
        "mode": "complex",
        "filter_status": filter_status,
        "total_cases": total_cases,
        "continuation_rate": safe_round(c1_analysis.get("green_rate"), 2),
        "reversal_rate": safe_round(c1_analysis.get("red_rate"), 2),
        "continuation_count": c1_analysis.get("green_count", 0),
        "reversal_count": c1_analysis.get("red_count", 0),
        "avg_body_pct": None,
        "continuation_ci": (
            {
                "ci_lower": c1_analysis.get("green_confidence_interval", [None, None])[0],
                "ci_upper": c1_analysis.get("green_confidence_interval", [None, None])[1],
            }
            if c1_analysis.get("green_confidence_interval")
            else None
        ),
        "c1_p_value": None,
        "c1_is_significant": False,
        "c2_after_c1_green_rate": safe_round(c2_analysis.get("green_rate"), 2),
        "c2_after_c1_red_rate": safe_round(c2_analysis.get("red_rate"), 2),
        "c2_after_c1_green_ci": (
            {
                "ci_lower": c2_analysis.get("green_confidence_interval", [None, None])[0],
                "ci_upper": c2_analysis.get("green_confidence_interval", [None, None])[1],
            }
            if c2_analysis.get("green_confidence_interval")
            else None
        ),
        "c2_after_c1_red_ci": (
            {
                "ci_lower": c2_analysis.get("red_confidence_interval", [None, None])[0],
                "ci_upper": c2_analysis.get("red_confidence_interval", [None, None])[1],
            }
            if c2_analysis.get("red_confidence_interval")
            else None
        ),
        "c1_green_count": c1_analysis.get("green_count", 0),
        "c1_red_count": c1_analysis.get("red_count", 0),
        "comparative_report": complex_pattern_analysis.get("comparative_report"),
        "short_signal": complex_pattern_analysis.get("short_signal"),
        "volatility_stats": complex_pattern_analysis.get("volatility_stats"),
        "rsi_by_interval": complex_pattern_analysis.get("rsi_by_interval", {}),
        "disp_by_interval": complex_pattern_analysis.get("disp_by_interval", {}),
        "atr_by_interval": complex_pattern_analysis.get("atr_by_interval", {}),
        "rsi_atr_heatmap": complex_pattern_analysis.get("rsi_atr_heatmap"),
        "high_prob_rsi_intervals": complex_pattern_analysis.get("high_prob_rsi_intervals", {}),
        "high_prob_disp_intervals": complex_pattern_analysis.get("high_prob_disp_intervals", {}),
        "high_prob_atr_intervals": complex_pattern_analysis.get("high_prob_atr_intervals", {}),
        "complex_pattern_analysis": complex_pattern_analysis,
        "ny_trading_guide": None,
        "analysis_mode": {
            "type": "complex",
            "description": "Complex Pattern with Pullback",
            "parameters": {
                "complex_pattern": complex_pattern,
                "filters": {
                    "rsi_threshold": context.rsi_threshold,
                    "ema_200_position": context.ema_200_position,
                },
            },
        },
        "from_cache": from_cache,
        "coin": context.coin,
        "interval": context.interval,
        "n_streak": None,
        "direction": context.direction,
    }


__all__ = [
    "build_complex_filter_status",
    "build_complex_success_result",
    "build_empty_complex_result",
    "build_filtered_out_complex_result",
    "build_no_match_complex_result",
    "build_quality_failure_result",
]
