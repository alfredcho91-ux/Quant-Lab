"""Pure math and statistics functions for AI lab."""

from __future__ import annotations

from typing import Optional

import pandas as pd


def _reliability_label(sample_count: int) -> str:
    if sample_count < 10:
        return "Low Reliability"
    if sample_count < 30:
        return "Medium Reliability"
    return "High Reliability"


def _safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _calculate_gati_index(
    probability_rate: Optional[float],
    p_value: Optional[float],
    sample_count: int,
    reliability: str,
) -> float:
    probability = _safe_float(probability_rate)
    if probability is None or sample_count <= 0:
        return 0.0

    edge_score = min(100.0, abs(probability - 50.0) * 2.0)
    p_val = _safe_float(p_value)
    significance_score = 0.0 if p_val is None else max(0.0, min(100.0, (1.0 - min(1.0, max(0.0, p_val))) * 100.0))
    sample_score = max(0.0, min(100.0, sample_count / 120.0 * 100.0))
    reliability_score = {
        "Low Reliability": 35.0,
        "Medium Reliability": 65.0,
        "High Reliability": 90.0,
    }.get(reliability, 50.0)

    gati = (
        edge_score * 0.45
        + significance_score * 0.25
        + sample_score * 0.20
        + reliability_score * 0.10
    )
    return round(max(0.0, min(100.0, gati)), 2)


def _p_value_reliability_label(p_value: Optional[float]) -> str:
    val = _safe_float(p_value)
    if val is None:
        return "N/A"
    if val < 0.01:
        return "Very High"
    if val < 0.05:
        return "High"
    if val < 0.1:
        return "Medium"
    return "Low"
