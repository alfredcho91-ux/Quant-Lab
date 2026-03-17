"""Facade for AI backtest optimization helpers."""

from __future__ import annotations

from .optimization_analysis import (
    build_optimization_characteristics,
    build_ui_result_from_advanced_payload,
    extract_advanced_summary,
    format_optimization_summary,
    normalize_summary_for_ui,
    score_advanced_backtest,
    score_backtest_summary,
    to_advanced_params,
)
from .optimization_runner import run_backtest_parameter_optimization
from .optimization_space import (
    build_float_candidates,
    build_int_candidates,
    build_optimization_rng,
    build_optimization_space,
    generate_optimization_candidates,
    optimization_signature,
)

__all__ = [
    "build_float_candidates",
    "build_int_candidates",
    "build_optimization_rng",
    "build_optimization_space",
    "build_optimization_characteristics",
    "build_ui_result_from_advanced_payload",
    "extract_advanced_summary",
    "format_optimization_summary",
    "generate_optimization_candidates",
    "normalize_summary_for_ui",
    "optimization_signature",
    "run_backtest_parameter_optimization",
    "score_advanced_backtest",
    "score_backtest_summary",
    "to_advanced_params",
]
