"""Workflow orchestration for complex streak analysis."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Dict

import pandas as pd

from strategy.context import AnalysisContext
from strategy.streak.analyzer import calculate_complex_analysis
from strategy.streak.common import (
    analyze_pullback_quality,
    find_complex_pattern,
    get_or_calculate_indicators,
    sanitize_for_json,
)
from strategy.streak.complex_processing import filter_and_score_patterns
from strategy.streak.complex_results import (
    build_complex_filter_status,
    build_complex_success_result,
    build_empty_complex_result,
    build_filtered_out_complex_result,
    build_no_match_complex_result,
    build_quality_failure_result,
)
from strategy.streak.data_ops import filter_rows_by_ema_200_position
from strategy.streak.patterns import build_pattern_profile

logger = logging.getLogger(__name__)


def run_complex_analysis(
    df: pd.DataFrame,
    context: AnalysisContext,
    from_cache: bool = False,
) -> Dict[str, Any]:
    try:
        df = get_or_calculate_indicators(context.coin, context.interval, df)

        pattern_profile = build_pattern_profile(context.complex_pattern)
        if pattern_profile is None:
            return build_empty_complex_result(context, from_cache)
        complex_pattern = pattern_profile.pattern

        matched_patterns = find_complex_pattern(df, complex_pattern)
        total_matches = len(matched_patterns)
        if total_matches == 0:
            return build_no_match_complex_result(context, complex_pattern, from_cache)

        matched_patterns = filter_rows_by_ema_200_position(
            df=df,
            rows=matched_patterns,
            ema_200_position=context.ema_200_position,
        )
        if matched_patterns.empty:
            return build_filtered_out_complex_result(
                context,
                complex_pattern,
                from_cache,
                total_matches,
            )

        quality_results = analyze_pullback_quality(
            df,
            matched_patterns.index,
            rise_len=pattern_profile.rise_len,
            drop_len=pattern_profile.drop_len,
        )
        if len(quality_results) == 0:
            return build_quality_failure_result(
                total_matches=total_matches,
                complex_pattern=complex_pattern,
                from_cache=from_cache,
            )

        filtered_indices, chart_data, scored_patterns = filter_and_score_patterns(
            df,
            quality_results,
            expected_c1_direction=pattern_profile.expected_c1_direction,
            last_pattern_direction=pattern_profile.last_direction,
        )
        filter_status = build_complex_filter_status(
            total_matches=total_matches,
            quality_result_count=len(quality_results),
            filtered_count=len(filtered_indices),
            ema_200_position=context.ema_200_position,
        )

        complex_pattern_analysis = calculate_complex_analysis(
            df,
            complex_pattern,
            matched_patterns,
            scored_patterns,
            chart_data,
            context,
        )
        result = build_complex_success_result(
            context=context,
            complex_pattern=complex_pattern,
            from_cache=from_cache,
            total_cases=len(filtered_indices),
            filter_status=filter_status,
            complex_pattern_analysis=complex_pattern_analysis,
        )
        return sanitize_for_json(result)
    except Exception as exc:
        logger.error("Error in run_complex_analysis: %s\n%s", exc, traceback.format_exc())
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {str(exc)}",
            "traceback": traceback.format_exc(),
            "mode": "complex",
        }


__all__ = ["run_complex_analysis"]
