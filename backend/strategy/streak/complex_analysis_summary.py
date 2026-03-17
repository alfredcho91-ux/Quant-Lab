"""Summary builder for complex streak analysis payloads."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from strategy.context import AnalysisContext
from strategy.streak.common import DEBUG_MODE
from strategy.streak.matcher import build_chart_positions
from utils.stats import wilson_confidence_interval

from .complex_analysis_details import (
    calculate_comparative_report,
    calculate_interval_analysis,
    calculate_short_signal,
    calculate_volatility_stats,
)


def _calculate_score_summary(scored_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scored_patterns:
        return {
            "avg_score": 0,
            "high_confidence_count": 0,
            "high_confidence_rate": 0,
        }

    scores = [p["score"] for p in scored_patterns]
    high_confidence_count = sum(1 for p in scored_patterns if p.get("confidence") == "high")
    return {
        "avg_score": round(sum(scores) / len(scores), 2),
        "high_confidence_count": high_confidence_count,
        "high_confidence_rate": round(high_confidence_count / len(scored_patterns) * 100, 2),
    }


def _summarize_candle_outcomes(
    chart_data: List[Dict[str, Any]],
    *,
    prefix: str,
) -> Dict[str, Any]:
    direction_key = f"{prefix}_direction"
    success_key = f"is_success_{prefix}"
    profit_key = f"profit_{prefix}"

    green_count = 0
    red_count = 0
    total_count = 0
    success_count = 0
    profit_sum = 0.0

    for row in chart_data:
        direction = row.get(direction_key)
        if direction is None:
            continue

        total_count += 1
        if direction == 1:
            green_count += 1
        elif direction == -1:
            red_count += 1

        if row.get(success_key):
            success_count += 1

        profit = row.get(profit_key)
        if profit is not None:
            profit_sum += profit

    green_rate = (green_count / total_count * 100) if total_count > 0 else 0
    red_rate = (red_count / total_count * 100) if total_count > 0 else 0
    win_rate = (success_count / total_count * 100) if total_count > 0 else 0

    return {
        "green_rate": round(green_rate, 2),
        "red_rate": round(red_rate, 2),
        "green_confidence_interval": wilson_confidence_interval(green_count, total_count) if total_count > 0 else None,
        "red_confidence_interval": wilson_confidence_interval(red_count, total_count) if total_count > 0 else None,
        "green_count": green_count,
        "red_count": red_count,
        "total_count": total_count,
        "avg_return": round(profit_sum / total_count, 2) if total_count > 0 else 0,
        "pattern_based_win_rate": round(win_rate, 2) if DEBUG_MODE else None,
        "pattern_based_confidence_interval": (
            [
                wilson_confidence_interval(success_count, total_count)["ci_lower"],
                wilson_confidence_interval(success_count, total_count)["ci_upper"],
            ]
            if total_count > 0 and DEBUG_MODE
            else None
        ),
    }


def calculate_complex_analysis(
    df: pd.DataFrame,
    complex_pattern: List[int],
    matched_patterns: pd.DataFrame,
    scored_patterns: List[Dict[str, Any]],
    chart_data: List[Dict[str, Any]],
    context: AnalysisContext,
) -> Dict[str, Any]:
    score_summary = _calculate_score_summary(scored_patterns)
    c1_summary = _summarize_candle_outcomes(chart_data, prefix="c1")
    c2_summary = _summarize_candle_outcomes(chart_data, prefix="c2")

    chart_positions = build_chart_positions(df, chart_data)
    volatility_stats = calculate_volatility_stats(df, chart_data, chart_positions=chart_positions)
    short_signal = calculate_short_signal(df, complex_pattern, chart_data, chart_positions=chart_positions)
    (
        rsi_by_interval,
        high_prob_rsi,
        retracement_by_interval,
        high_prob_retracement,
        disp_by_interval,
        high_prob_disp,
        atr_by_interval,
        high_prob_atr,
        rsi_atr_heatmap,
    ) = calculate_interval_analysis(df, chart_data, chart_positions=chart_positions)
    comparative_report = calculate_comparative_report(chart_data)

    return {
        "pattern": complex_pattern,
        "total_matches": len(matched_patterns),
        "analyzed_count": len(scored_patterns),
        "filtered_count": len(chart_data),
        "avg_score": score_summary["avg_score"],
        "high_confidence_count": score_summary["high_confidence_count"],
        "high_confidence_rate": score_summary["high_confidence_rate"],
        "patterns": scored_patterns[:10],
        "ny_trading_guide": None,
        "chart_data": chart_data,
        "summary": {
            "c1_analysis": c1_summary,
            "c2_analysis": c2_summary,
        },
        "filters_applied": {"rsi_threshold": context.rsi_threshold},
        "short_signal": short_signal,
        "volatility_stats": volatility_stats,
        "rsi_by_interval": rsi_by_interval,
        "disp_by_interval": disp_by_interval,
        "atr_by_interval": atr_by_interval,
        "rsi_atr_heatmap": rsi_atr_heatmap,
        "retracement_by_interval": retracement_by_interval,
        "high_prob_rsi_intervals": high_prob_rsi,
        "high_prob_disp_intervals": high_prob_disp,
        "high_prob_atr_intervals": high_prob_atr,
        "high_prob_retracement_intervals": high_prob_retracement,
        "comparative_report": comparative_report,
    }


__all__ = ["calculate_complex_analysis"]
