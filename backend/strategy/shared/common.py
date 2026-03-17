"""Shared strategy statistics helpers.

This module is domain-agnostic and must not import streak-specific modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from utils.stats import safe_float


def calculate_sharpe_ratio_unified(
    returns: pd.Series,
    period: str = "daily",
    risk_free_rate: float = 0.0,
) -> Optional[float]:
    if len(returns) == 0:
        return None

    excess_returns = returns - risk_free_rate
    if excess_returns.std() == 0:
        return None

    annualization_factors = {
        "daily": np.sqrt(252),
        "weekly": np.sqrt(52),
        "monthly": np.sqrt(12),
    }
    factor = annualization_factors.get(period, np.sqrt(252))
    sharpe = excess_returns.mean() / excess_returns.std() * factor
    return safe_float(sharpe)


def calculate_max_drawdown_unified(
    returns: pd.Series,
    method: str = "cumprod",
) -> Dict[str, Any]:
    if len(returns) == 0:
        return {"max_drawdown": None, "max_drawdown_pct": None}

    if method == "cumprod":
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        max_dd_pct = safe_float(max_dd * 100) if max_dd is not None else None
    else:
        cumulative = returns.cumsum()
        peak = np.maximum.accumulate(cumulative)
        drawdown = peak - cumulative
        max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0.0
        max_dd_pct = (
            float(max_dd / (np.max(peak) + 1e-10) * 100) if np.max(peak) > 0 else 0.0
        )

    return {
        "max_drawdown": safe_float(max_dd),
        "max_drawdown_pct": max_dd_pct,
    }


def calculate_t_test_unified(returns: pd.Series) -> Dict[str, Any]:
    if len(returns) < 2:
        return {"t_statistic": None, "p_value": None, "is_significant": False}

    t_stat, p_value = scipy_stats.ttest_1samp(returns, 0.0)
    return {
        "t_statistic": safe_float(t_stat),
        "p_value": safe_float(p_value),
        "is_significant": bool(p_value is not None and p_value < 0.05),
    }


def calculate_profit_factor(returns: pd.Series) -> Optional[float]:
    if len(returns) == 0:
        return None

    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    if gross_loss == 0:
        return None

    pf = gross_profit / gross_loss
    return safe_float(pf) if not np.isinf(pf) and not np.isnan(pf) else None


def calculate_max_consecutive_loss(returns: pd.Series) -> int:
    if len(returns) == 0:
        return 0

    max_consecutive = 0
    current_consecutive = 0
    for ret in returns:
        if ret < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    return max_consecutive


def calculate_returns_confidence_interval(
    returns: pd.Series,
    confidence: float = 0.95,
) -> Dict[str, Any]:
    if len(returns) == 0:
        return {"ci_lower": None, "ci_upper": None, "ci_width": None}

    mean = returns.mean()
    std = returns.std()
    n = len(returns)
    if n < 2 or std == 0:
        fixed = safe_float(mean * 100)
        return {"ci_lower": fixed, "ci_upper": fixed, "ci_width": 0.0}

    t_value = scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1)
    margin = t_value * std / np.sqrt(n)
    ci_lower = (mean - margin) * 100
    ci_upper = (mean + margin) * 100
    return {
        "ci_lower": safe_float(ci_lower),
        "ci_upper": safe_float(ci_upper),
        "ci_width": safe_float(ci_upper - ci_lower),
    }


__all__ = [
    "calculate_sharpe_ratio_unified",
    "calculate_max_drawdown_unified",
    "calculate_t_test_unified",
    "calculate_profit_factor",
    "calculate_max_consecutive_loss",
    "calculate_returns_confidence_interval",
]

