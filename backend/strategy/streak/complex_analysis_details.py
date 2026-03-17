"""Detailed calculators for complex streak analysis payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from strategy.streak.common import (
    ATR_BINS,
    CONFIDENCE_LEVEL,
    DEFAULT_RSI,
    DISP_BINS,
    RETRACEMENT_BINS,
    RSI_BINS,
    RSI_OVERBOUGHT,
    safe_get_rsi,
    safe_round,
)
from strategy.streak.matcher import build_chart_positions
from strategy.streak.statistics import (
    analyze_2d_interval_heatmap,
    analyze_interval_statistics,
    trimmed_stats,
)
from utils.stats import safe_float


def calculate_volatility_stats(
    df: pd.DataFrame,
    chart_data: List[Dict[str, Any]],
    chart_positions: Optional[List[Tuple[Dict[str, Any], int]]] = None,
) -> Optional[Dict[str, Any]]:
    if len(chart_data) == 0:
        return None

    if chart_positions is None:
        chart_positions = build_chart_positions(df, chart_data)
    if len(chart_positions) == 0:
        return None

    c1_cases = []
    for _, pos in chart_positions:
        if pos + 1 < len(df):
            c1_row = df.iloc[pos + 1]
            c1_cases.append(
                {
                    "open": c1_row["open"],
                    "high": c1_row["high"],
                    "low": c1_row["low"],
                    "close": c1_row["close"],
                    "atr_pct": c1_row.get("atr_pct", 0),
                }
            )

    if len(c1_cases) == 0:
        return None

    c1_df = pd.DataFrame(c1_cases)
    c1_df["max_dip"] = (c1_df["open"] - c1_df["low"]) / c1_df["open"] * 100
    c1_df["max_rise"] = (c1_df["high"] - c1_df["open"]) / c1_df["open"] * 100

    dip_stats = trimmed_stats(c1_df["max_dip"])
    rise_stats = trimmed_stats(c1_df["max_rise"])
    avg_atr = safe_float(c1_df["atr_pct"].mean()) if len(c1_df) > 0 else None

    return {
        "avg_dip": safe_round(dip_stats["mean"], 2),
        "avg_rise": safe_round(rise_stats["mean"], 2),
        "std_dip": safe_round(dip_stats["std"], 2),
        "avg_atr_pct": safe_round(avg_atr, 2),
        "practical_max_dip": safe_round(dip_stats["max"], 2),
        "extreme_max_dip": safe_round(dip_stats.get("original_max", 0), 2),
        "is_trimmed": dip_stats["trimmed"],
        "sample_count": len(c1_cases),
    }


def calculate_short_signal(
    df: pd.DataFrame,
    complex_pattern: List[int],
    chart_data: List[Dict[str, Any]],
    chart_positions: Optional[List[Tuple[Dict[str, Any], int]]] = None,
) -> Optional[Dict[str, Any]]:
    if len(complex_pattern) == 0 or complex_pattern[-1] != 1:
        return None

    if chart_positions is None:
        chart_positions = build_chart_positions(df, chart_data)

    short_candidates = []
    for c, pattern_pos in chart_positions:
        rsi_val = c.get("rsi")
        if rsi_val is None or rsi_val < RSI_OVERBOUGHT:
            continue
        if pattern_pos + 1 < len(df):
            c1_row = df.iloc[pattern_pos + 1]
            short_candidates.append(
                {
                    "open": c1_row["open"],
                    "high": c1_row["high"],
                    "close": c1_row["close"],
                    "rsi": rsi_val,
                }
            )

    if len(short_candidates) < 3:
        return None

    short_df = pd.DataFrame(short_candidates)
    short_df["max_rise"] = (short_df["high"] - short_df["open"]) / short_df["open"] * 100
    avg_rise_short = float(short_df["max_rise"].mean())

    target_entry_rise = max(0.1, avg_rise_short * 0.6)
    short_df["entry_threshold"] = short_df["open"] * (1 + target_entry_rise / 100)
    short_df["is_filled"] = short_df["high"] >= short_df["entry_threshold"]

    total_signals = len(short_df)
    filled_cases = short_df[short_df["is_filled"]].copy()
    fill_rate = (len(filled_cases) / total_signals * 100) if total_signals > 0 else 0

    if len(filled_cases) == 0:
        return None

    filled_cases["is_win"] = filled_cases["close"] < filled_cases["entry_threshold"]
    short_win_count = int(filled_cases["is_win"].sum())
    short_win_rate = (short_win_count / len(filled_cases)) * 100 if len(filled_cases) > 0 else 0

    filled_cases["pnl_pct"] = (
        (filled_cases["entry_threshold"] - filled_cases["close"]) / filled_cases["entry_threshold"] * 100
    )
    wins = filled_cases[filled_cases["pnl_pct"] > 0]
    avg_profit = float(wins["pnl_pct"].mean()) if len(wins) > 0 else 0
    overall_win_rate = (short_win_count / total_signals * 100) if total_signals > 0 else 0

    reliability = "high" if fill_rate >= 70 else "medium" if fill_rate >= 50 else "low"
    bias_warning = fill_rate < 50

    return {
        "enabled": short_win_rate >= 60 and fill_rate >= 50,
        "total_signals": total_signals,
        "filled_cases": len(filled_cases),
        "unfilled_cases": len(short_df) - len(filled_cases),
        "fill_rate": round(fill_rate, 2),
        "win_count": short_win_count,
        "win_rate": round(short_win_rate, 2),
        "overall_win_rate": round(overall_win_rate, 2),
        "entry_rise_pct": round(target_entry_rise, 2),
        "take_profit_pct": round(avg_profit, 2),
        "stop_loss_pct": 2.0,
        "rsi_threshold": RSI_OVERBOUGHT,
        "reliability": reliability,
        "bias_warning": bias_warning,
        "note": "Complex Pattern Based: All signals tracked, only filled cases analyzed",
    }


def calculate_interval_analysis(
    df: pd.DataFrame,
    chart_data: List[Dict[str, Any]],
    chart_positions: Optional[List[Tuple[Dict[str, Any], int]]] = None,
) -> tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Any],
]:
    empty_heatmap = {
        "x_label": "RSI",
        "y_label": "ATR%",
        "x_bins": [],
        "y_bins": [],
        "cells": {},
        "total_samples": 0,
        "tested_cells": 0,
        "significant_cells": 0,
    }

    if len(chart_data) == 0:
        return {}, {}, {}, {}, {}, {}, {}, {}, empty_heatmap

    if chart_positions is None:
        chart_positions = build_chart_positions(df, chart_data)

    pattern_rsi_vals = []
    pattern_retracement_vals = []
    pattern_disp_vals = []
    pattern_atr_vals = []
    pattern_is_green_vals = []

    for c, pos in chart_positions:
        if pos + 1 >= len(df):
            continue
        c1_row = df.iloc[pos + 1]

        pattern_idx = df.index[pos]
        pattern_rsi = safe_get_rsi(df, pattern_idx, DEFAULT_RSI)
        pattern_retracement = c.get("retracement", 50)
        row = df.iloc[pos]
        pattern_disp = safe_float(row.get("disparity"))
        pattern_atr = safe_float(row.get("atr_pct"))

        pattern_rsi_vals.append(pattern_rsi)
        pattern_retracement_vals.append(pattern_retracement)
        pattern_disp_vals.append(pattern_disp)
        pattern_atr_vals.append(pattern_atr)
        pattern_is_green_vals.append(1 if c1_row["close"] > c1_row["open"] else 0)

    if len(pattern_rsi_vals) == 0:
        return {}, {}, {}, {}, {}, {}, {}, {}, empty_heatmap

    rsi_by_interval, high_prob_rsi = analyze_interval_statistics(
        pd.Series(pattern_rsi_vals),
        pd.Series(pattern_is_green_vals),
        RSI_BINS,
        CONFIDENCE_LEVEL,
    )
    retracement_by_interval, high_prob_retracement = analyze_interval_statistics(
        pd.Series(pattern_retracement_vals),
        pd.Series(pattern_is_green_vals),
        RETRACEMENT_BINS,
        CONFIDENCE_LEVEL,
    )
    disp_by_interval, high_prob_disp = analyze_interval_statistics(
        pd.Series(pattern_disp_vals),
        pd.Series(pattern_is_green_vals),
        DISP_BINS,
        CONFIDENCE_LEVEL,
    )
    atr_by_interval, high_prob_atr = analyze_interval_statistics(
        pd.Series(pattern_atr_vals),
        pd.Series(pattern_is_green_vals),
        ATR_BINS,
        CONFIDENCE_LEVEL,
    )
    rsi_atr_heatmap = analyze_2d_interval_heatmap(
        pd.Series(pattern_rsi_vals),
        pd.Series(pattern_atr_vals),
        pd.Series(pattern_is_green_vals),
        RSI_BINS,
        ATR_BINS,
        x_label="RSI",
        y_label="ATR%",
        confidence=CONFIDENCE_LEVEL,
    )

    return (
        rsi_by_interval,
        high_prob_rsi,
        retracement_by_interval,
        high_prob_retracement,
        disp_by_interval,
        high_prob_disp,
        atr_by_interval,
        high_prob_atr,
        rsi_atr_heatmap,
    )


def calculate_comparative_report(chart_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(chart_data) == 0:
        return None

    success_cases = [c for c in chart_data if c.get("is_success_c1") is True]
    failure_cases = [c for c in chart_data if c.get("is_success_c1") is False]

    if len(success_cases) == 0 and len(failure_cases) == 0:
        return None

    def safe_mean_metric(cases: List[Dict[str, Any]], metric_key: str):
        vals = [c.get(metric_key) for c in cases if c.get(metric_key) is not None]
        return round(float(sum(vals) / len(vals)), 2) if len(vals) > 0 else None

    return {
        "pattern_total": len(chart_data),
        "success_count": len(success_cases),
        "failure_count": len(failure_cases),
        "success_rate": round(len(success_cases) / len(chart_data) * 100, 2) if len(chart_data) > 0 else None,
        "success": {
            "prev_rsi": safe_mean_metric(success_cases, "rsi"),
            "prev_body_pct": None,
            "prev_vol_change": safe_mean_metric(success_cases, "vol_ratio"),
        },
        "failure": {
            "prev_rsi": safe_mean_metric(failure_cases, "rsi"),
            "prev_body_pct": None,
            "prev_vol_change": safe_mean_metric(failure_cases, "vol_ratio"),
        },
    }


__all__ = [
    "calculate_comparative_report",
    "calculate_interval_analysis",
    "calculate_short_signal",
    "calculate_volatility_stats",
]
