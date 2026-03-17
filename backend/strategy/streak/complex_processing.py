"""Pattern filtering and chart-row builders for complex streak mode."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from strategy.streak.common import (
    DEBUG_MODE,
    DEFAULT_RSI,
    calculate_signal_score,
    normalize_single_index,
    safe_get_rsi,
)

logger = logging.getLogger(__name__)


def _build_followup_payloads(
    *,
    index_values: pd.Index,
    open_values,
    close_values,
    pattern_pos: int,
    df_len: int,
    expected_c1_direction: int,
) -> Tuple[Any, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    c1_pos = pattern_pos + 1
    if c1_pos >= df_len:
        return None, None, None

    c1_idx = index_values[c1_pos]
    c1_open = open_values[c1_pos]
    c1_close = close_values[c1_pos]
    base_close = close_values[pattern_pos]
    c1_color = 1 if c1_close > c1_open else -1
    c1_return = ((c1_close / base_close) - 1) * 100
    c1_data = {
        "date": str(c1_idx),
        "color": c1_color,
        "return": round(c1_return, 2),
        "is_success": c1_color == expected_c1_direction,
        "expected_direction": expected_c1_direction,
    }

    c2_pos = pattern_pos + 2
    if c2_pos >= df_len:
        return c1_idx, c1_data, None

    c2_idx = index_values[c2_pos]
    c2_open = open_values[c2_pos]
    c2_close = close_values[c2_pos]
    c2_color = 1 if c2_close > c2_open else -1
    c2_return = ((c2_close / c1_close) - 1) * 100
    c2_data = {
        "date": str(c2_idx),
        "color": c2_color,
        "return": round(c2_return, 2),
        "is_success": c2_color == expected_c1_direction,
        "expected_direction": expected_c1_direction,
    }
    return c1_idx, c1_data, c2_data


def filter_and_score_patterns(
    df: pd.DataFrame,
    quality_results: List[Dict[str, Any]],
    *,
    expected_c1_direction: int,
    last_pattern_direction: int,
) -> tuple[List[Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    filtered_indices = []
    chart_data = []
    scored_patterns = []

    df_len = len(df)
    index_values = df.index
    open_values = df["open"].to_numpy()
    close_values = df["close"].to_numpy()

    for quality in quality_results:
        idx = quality["index"]
        try:
            normalized = normalize_single_index(idx, df.index)
            if normalized is None:
                continue
            idx, pos = normalized

            rsi_val = safe_get_rsi(df, idx, DEFAULT_RSI)
            c1_idx, c1_data, c2_data = _build_followup_payloads(
                index_values=index_values,
                open_values=open_values,
                close_values=close_values,
                pattern_pos=pos,
                df_len=df_len,
                expected_c1_direction=expected_c1_direction,
            )
            if c1_idx is None or c1_data is None:
                continue

            score_data = calculate_signal_score(
                quality["retracement_pct"],
                quality["vol_ratio"],
                rsi_val,
            )
            scored_patterns.append(
                {
                    "index": str(idx),
                    "date": str(idx),
                    "retracement_pct": quality["retracement_pct"],
                    "vol_ratio": quality["vol_ratio"],
                    "rsi": round(rsi_val, 2),
                    **score_data,
                }
            )
            chart_data.append(
                {
                    "date": str(idx),
                    "pattern_date": str(idx),
                    "pattern_pos": pos,
                    "retracement": quality["retracement_pct"],
                    "vol_ratio": quality["vol_ratio"],
                    "rsi": round(rsi_val, 2),
                    "score": score_data["score"],
                    "confidence": score_data["confidence"],
                    "c1": c1_data,
                    "c2": c2_data,
                    "profit_c1": c1_data["return"] if c1_data else None,
                    "profit_c2": c2_data["return"] if c2_data else None,
                    "is_success_c1": c1_data["is_success"] if c1_data else None,
                    "is_success_c2": c2_data["is_success"] if c2_data else None,
                    "pattern_last_direction": last_pattern_direction,
                    "expected_c1_direction": expected_c1_direction,
                    "c1_direction": c1_data["color"] if c1_data else None,
                    "c2_direction": c2_data["color"] if c2_data else None,
                }
            )
            filtered_indices.append(c1_idx)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            if DEBUG_MODE:
                logger.debug("Error processing pattern at %s: %s", idx, exc)
            continue

    return filtered_indices, chart_data, scored_patterns


__all__ = ["filter_and_score_patterns"]
