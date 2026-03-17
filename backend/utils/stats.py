"""Shared statistical utility functions."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


CONFIDENCE_LEVEL = 0.95
P_VALUE_FLOOR = 1e-16


def safe_float(val: Any) -> Optional[float]:
    """Convert value to float while normalizing NaN/Infinity to None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
        float_val = float(val)
        if np.isnan(float_val) or np.isinf(float_val):
            return None
        return float_val
    except (ValueError, TypeError):
        return None


def wilson_confidence_interval(
    successes: int,
    total: int,
    confidence: float = CONFIDENCE_LEVEL,
) -> Dict[str, Any]:
    """Calculate Wilson-score confidence interval for binomial outcomes."""
    if total == 0:
        return {
            "rate": None,
            "ci_lower": None,
            "ci_upper": None,
            "ci_width": None,
        }

    p = successes / total
    z = scipy_stats.norm.ppf(1 - (1 - confidence) / 2)

    denominator = 1 + (z**2 / total)
    center = (p + (z**2 / (2 * total))) / denominator
    margin = (z / denominator) * np.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))

    ci_lower = max(0, center - margin) * 100
    ci_upper = min(1, center + margin) * 100

    return {
        "rate": safe_float(p * 100),
        "ci_lower": safe_float(ci_lower),
        "ci_upper": safe_float(ci_upper),
        "ci_width": safe_float(ci_upper - ci_lower),
    }


def calculate_binomial_pvalue(successes: int, total: int, null_prob: float = 0.5) -> float:
    """Calculate two-sided binomial test p-value."""
    if total == 0:
        return 1.0
    result = scipy_stats.binomtest(successes, total, null_prob, alternative="two-sided")
    return result.pvalue


__all__ = [
    "CONFIDENCE_LEVEL",
    "P_VALUE_FLOOR",
    "safe_float",
    "wilson_confidence_interval",
    "calculate_binomial_pvalue",
]
