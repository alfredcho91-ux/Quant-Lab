"""Statistics and payload builders for AI lab conditional probability analysis."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from .expression import _sorted_condition_specs
from .stats_math import (
    _calculate_gati_index,
    _p_value_reliability_label,
    _reliability_label,
    _safe_float,
)


def calculate_probability_summary(
    *,
    mask: pd.Series,
    target_series: pd.Series,
    calculate_binomial_pvalue_fn: Callable[..., Any],
    wilson_confidence_interval_fn: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    next_target = target_series.shift(-1)
    valid_mask = mask & next_target.notna()
    sample_count = int(valid_mask.sum())
    success_count = int((valid_mask & (next_target == True)).sum())
    failure_count = max(0, sample_count - success_count)

    probability_rate = (success_count / sample_count * 100.0) if sample_count > 0 else None
    ci = wilson_confidence_interval_fn(success_count, sample_count) if sample_count > 0 else {}
    ci_lower = _safe_float(ci.get("ci_lower"))
    ci_upper = _safe_float(ci.get("ci_upper"))
    p_value = (
        _safe_float(calculate_binomial_pvalue_fn(success_count, sample_count, null_prob=0.5))
        if sample_count > 0
        else None
    )
    reliability = _reliability_label(sample_count)
    gati_index = _calculate_gati_index(
        probability_rate=probability_rate,
        p_value=p_value,
        sample_count=sample_count,
        reliability=reliability,
    )
    success_rate = (success_count / sample_count * 100.0) if sample_count > 0 else 0.0
    failure_rate = 100.0 - success_rate if sample_count > 0 else 0.0

    return {
        "sample_count": sample_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "probability_rate": _safe_float(probability_rate),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_value": p_value,
        "p_value_reliability": _p_value_reliability_label(p_value),
        "reliability": reliability,
        "gati_index": gati_index,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
    }


def build_probability_analysis_result(
    *,
    coin: str,
    interval: str,
    source: str,
    target_side: str,
    condition_text: str,
    condition_specs: List[Dict[str, Any]],
    ignored_conditions: List[str],
    expression_tokens: List[str],
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    condition_components = [spec["component"] for spec in _sorted_condition_specs(condition_specs)]

    return {
        "analysis_type": "conditional_probability",
        "coin": coin,
        "interval": interval,
        "source": source,
        "condition": {
            "target_side": target_side,
            "condition_text": condition_text,
            "components": condition_components,
            "ignored_conditions": ignored_conditions,
            "expression_tokens": expression_tokens,
        },
        "summary": {
            "sample_count": summary["sample_count"],
            "success_count": summary["success_count"],
            "failure_count": summary["failure_count"],
            "probability_rate": summary["probability_rate"],
            "ci_lower": summary["ci_lower"],
            "ci_upper": summary["ci_upper"],
            "p_value": summary["p_value"],
            "p_value_reliability": summary["p_value_reliability"],
            "reliability": summary["reliability"],
            "gati_index": summary["gati_index"],
        },
        "outcome_bars": [
            {
                "key": "success",
                "label": "Success",
                "count": summary["success_count"],
                "rate_pct": round(summary["success_rate"], 2),
            },
            {
                "key": "failure",
                "label": "Failure",
                "count": summary["failure_count"],
                "rate_pct": round(summary["failure_rate"], 2),
            },
        ],
        "confidence_band": {
            "baseline": 50.0,
            "center": summary["probability_rate"],
            "lower": summary["ci_lower"],
            "upper": summary["ci_upper"],
        },
        "generated_at": pd.Timestamp.utcnow().isoformat(),
    }


__all__ = [
    "build_probability_analysis_result",
    "calculate_probability_summary",
]
