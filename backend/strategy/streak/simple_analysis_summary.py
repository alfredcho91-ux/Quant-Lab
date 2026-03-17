"""Summary builder for simple streak analysis payloads."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from strategy.context import AnalysisContext
from strategy.streak.common import (
    ATR_BINS,
    CONFIDENCE_LEVEL,
    DISP_BINS,
    RSI_BINS,
    extract_c1_indices,
    safe_round,
)
from strategy.streak.statistics import (
    analyze_2d_interval_heatmap,
    analyze_interval_statistics,
    trimmed_stats,
)
from utils.stats import (
    calculate_binomial_pvalue,
    safe_float,
    wilson_confidence_interval,
)

from .simple_analysis_details import calculate_comparative_report, calculate_short_signal


def calculate_simple_metrics(
    df: pd.DataFrame,
    target_cases: pd.DataFrame,
    context: AnalysisContext,
) -> Dict[str, Any]:
    """Calculate simple-mode analytics payload from prepared target cases."""
    total_cases = len(target_cases)
    is_bullish_pattern = context.direction == "green"

    df_work = df.copy()
    df_work["next_is_green"] = df_work["is_green"].shift(-1)

    c1_green_mask = df_work.loc[target_cases.index, "next_is_green"] == True
    c1_red_mask = df_work.loc[target_cases.index, "next_is_green"] == False

    if is_bullish_pattern:
        continuation_count = int(c1_green_mask.sum())
        reversal_count = int(c1_red_mask.sum())
    else:
        continuation_count = int(c1_red_mask.sum())
        reversal_count = int(c1_green_mask.sum())

    continuation_rate = float(continuation_count / total_cases * 100) if total_cases > 0 else 0
    reversal_rate = 100 - continuation_rate
    continuation_ci = wilson_confidence_interval(continuation_count, total_cases)
    c1_pvalue = calculate_binomial_pvalue(continuation_count, total_cases, 0.5)

    c1_continuation_indices = extract_c1_indices(df_work, target_cases.index, filter_green=is_bullish_pattern)
    c1_reversal_indices = extract_c1_indices(df_work, target_cases.index, filter_green=not is_bullish_pattern)

    if len(c1_continuation_indices) > 0:
        continuations = df_work.loc[c1_continuation_indices]
        avg_body_pct = float(continuations["body_pct"].mean())
        max_body_pct = float(continuations["body_pct"].max())
        min_body_pct = float(continuations["body_pct"].min())
    else:
        avg_body_pct = 0
        max_body_pct = None
        min_body_pct = None

    if len(c1_reversal_indices) > 0:
        reversals = df_work.loc[c1_reversal_indices]
        reversal_body_pct = (
            reversals["body_pct"]
            if is_bullish_pattern
            else (reversals["close"] - reversals["open"]) / reversals["open"] * 100
        )
        avg_reversal_body_pct = float(reversal_body_pct.mean())
        max_reversal_body_pct = float(reversal_body_pct.max())
        min_reversal_body_pct = float(reversal_body_pct.min())
    else:
        avg_reversal_body_pct = None
        max_reversal_body_pct = None
        min_reversal_body_pct = None

    c1_green_cases = target_cases[c1_green_mask]
    c1_red_cases = target_cases[c1_red_mask]
    c1_green_count = len(c1_green_cases)
    c1_red_count = len(c1_red_cases)
    c1_green_rate = (c1_green_count / total_cases * 100) if total_cases > 0 else 0
    c1_red_rate = (c1_red_count / total_cases * 100) if total_cases > 0 else 0
    c1_green_rate_ci = wilson_confidence_interval(c1_green_count, total_cases) if total_cases > 0 else None
    c1_red_rate_ci = wilson_confidence_interval(c1_red_count, total_cases) if total_cases > 0 else None

    c2_after_c1_green_rate = None
    c2_after_c1_red_rate = None
    c2_after_c1_green_ci = None
    c2_after_c1_red_ci = None

    if c1_green_count > 0:
        c1_green_indices = extract_c1_indices(df_work, c1_green_cases.index, filter_green=True)
        if len(c1_green_indices) > 0:
            c2_vals = df_work.loc[c1_green_indices, "next_is_green"].dropna()
            if len(c2_vals) > 0:
                c2_green_success = int(c2_vals.sum())
                c2_after_c1_green_rate = float(c2_vals.mean() * 100)
                c2_after_c1_green_ci = wilson_confidence_interval(c2_green_success, len(c2_vals))

    if c1_red_count > 0:
        c1_red_indices = extract_c1_indices(df_work, c1_red_cases.index, filter_green=False)
        if len(c1_red_indices) > 0:
            c2_vals = df_work.loc[c1_red_indices, "next_is_green"].dropna()
            if len(c2_vals) > 0:
                c2_red_success = int(c2_vals.sum())
                c2_after_c1_red_rate = float(c2_vals.mean() * 100)
                c2_after_c1_red_ci = wilson_confidence_interval(c2_red_success, len(c2_vals))

    comparative_report = calculate_comparative_report(df_work, context.n_streak, context.direction)

    tc = target_cases.copy()
    tc["rsi"] = df_work.loc[tc.index, "rsi"]
    tc["atr_pct"] = df_work.loc[tc.index, "atr_pct"]
    tc["max_dip"] = (tc["open"] - tc["low"]) / tc["open"] * 100
    tc["max_rise"] = (tc["high"] - tc["open"]) / tc["open"] * 100

    dip_stats = trimmed_stats(tc["max_dip"])
    rise_stats = trimmed_stats(tc["max_rise"])
    atr_stats = trimmed_stats(tc["atr_pct"].dropna())

    avg_dip = dip_stats["mean"]
    std_dip = dip_stats["std"]
    avg_rise = rise_stats["mean"]
    avg_atr_pct = atr_stats["mean"]

    z_score_dip = None
    current_dip = None
    if len(tc) > 0 and std_dip is not None and std_dip > 0:
        current_dip = safe_float(tc["max_dip"].iloc[-1])
        if current_dip is not None and avg_dip is not None:
            z_score_dip = safe_round((current_dip - avg_dip) / std_dip, 2)

    z_score_interpretation = None
    if z_score_dip is not None:
        if abs(z_score_dip) < 1:
            z_score_interpretation = "normal"
        elif abs(z_score_dip) < 2:
            z_score_interpretation = "unusual"
        else:
            z_score_interpretation = "extreme"

    volatility_stats = {
        "avg_dip": safe_round(avg_dip, 2),
        "avg_rise": safe_round(avg_rise, 2),
        "std_dip": safe_round(std_dip, 2),
        "avg_atr_pct": safe_round(avg_atr_pct, 2),
        "practical_max_dip": safe_round(dip_stats["max"], 2),
        "extreme_max_dip": safe_round(dip_stats.get("original_max", 0), 2),
        "current_dip": safe_round(current_dip, 2),
        "z_score_dip": z_score_dip,
        "z_score_interpretation": z_score_interpretation,
        "is_trimmed": dip_stats["trimmed"],
        "sample_count": len(tc),
    }

    short_signal = None
    if context.direction == "green":
        short_signal = calculate_short_signal(df_work, context.n_streak, avg_rise)

    pattern_rsi = df_work["rsi"].loc[tc.index]
    next_is_green_series = df_work.loc[tc.index, "next_is_green"].astype("boolean")
    next_is_green = next_is_green_series.fillna(False).astype("bool", copy=False)
    rsi_by_interval, high_prob_rsi = analyze_interval_statistics(
        pattern_rsi,
        next_is_green,
        RSI_BINS,
        CONFIDENCE_LEVEL,
    )
    pattern_disp = df_work["disparity"].loc[tc.index]
    disp_by_interval, high_prob_disp = analyze_interval_statistics(
        pattern_disp,
        next_is_green,
        DISP_BINS,
        CONFIDENCE_LEVEL,
    )
    pattern_atr = df_work["atr_pct"].loc[tc.index]
    atr_by_interval, high_prob_atr = analyze_interval_statistics(
        pattern_atr,
        next_is_green,
        ATR_BINS,
        CONFIDENCE_LEVEL,
    )
    rsi_atr_heatmap = analyze_2d_interval_heatmap(
        pattern_rsi,
        pattern_atr,
        next_is_green,
        RSI_BINS,
        ATR_BINS,
        x_label="RSI",
        y_label="ATR%",
        confidence=CONFIDENCE_LEVEL,
    )

    return {
        "total_cases": total_cases,
        "continuation_rate": safe_round(continuation_rate, 2),
        "reversal_rate": safe_round(reversal_rate, 2),
        "continuation_count": continuation_count,
        "reversal_count": reversal_count,
        "avg_body_pct": safe_round(avg_body_pct, 2),
        "continuation_stats": {
            "avg_body_pct": safe_round(avg_body_pct, 2) if avg_body_pct else None,
            "max_body_pct": safe_round(max_body_pct, 2) if max_body_pct is not None else None,
            "min_body_pct": safe_round(min_body_pct, 2) if min_body_pct is not None else None,
            "count": continuation_count,
        },
        "reversal_stats": {
            "avg_body_pct": safe_round(avg_reversal_body_pct, 2) if avg_reversal_body_pct is not None else None,
            "max_body_pct": safe_round(max_reversal_body_pct, 2) if max_reversal_body_pct is not None else None,
            "min_body_pct": safe_round(min_reversal_body_pct, 2) if min_reversal_body_pct is not None else None,
            "count": reversal_count,
        },
        "continuation_ci": continuation_ci,
        "c1_p_value": safe_round(c1_pvalue, 4),
        "c1_is_significant": bool(c1_pvalue < 0.05) if c1_pvalue is not None else False,
        "c2_after_c1_green_rate": safe_round(c2_after_c1_green_rate, 2),
        "c2_after_c1_red_rate": safe_round(c2_after_c1_red_rate, 2),
        "c2_after_c1_green_ci": c2_after_c1_green_ci,
        "c2_after_c1_red_ci": c2_after_c1_red_ci,
        "c1_green_count": c1_green_count,
        "c1_red_count": c1_red_count,
        "c1_green_rate": safe_round(c1_green_rate, 2),
        "c1_red_rate": safe_round(c1_red_rate, 2),
        "c1_green_rate_ci": c1_green_rate_ci,
        "c1_red_rate_ci": c1_red_rate_ci,
        "comparative_report": comparative_report,
        "short_signal": short_signal,
        "volatility_stats": volatility_stats,
        "rsi_by_interval": rsi_by_interval,
        "disp_by_interval": disp_by_interval,
        "atr_by_interval": atr_by_interval,
        "rsi_atr_heatmap": rsi_atr_heatmap,
        "high_prob_rsi_intervals": high_prob_rsi,
        "high_prob_disp_intervals": high_prob_disp,
        "high_prob_atr_intervals": high_prob_atr,
    }


__all__ = ["calculate_simple_metrics"]
