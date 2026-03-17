"""Optimization workflow orchestration for AI backtest lab."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from models.request import AdvancedBacktestParams, BacktestParams

from .optimization_analysis import (
    build_optimization_characteristics,
    build_ui_result_from_advanced_payload,
    extract_advanced_summary,
    format_optimization_summary,
    score_advanced_backtest,
    to_advanced_params,
)
from .optimization_space import generate_optimization_candidates


@dataclass
class OptimizationSearchState:
    best_params: Optional[BacktestParams] = None
    best_advanced_result: Optional[Dict[str, Any]] = None
    best_summary: Dict[str, Any] = field(default_factory=dict)
    base_summary: Dict[str, Any] = field(default_factory=dict)
    best_score: float = float("-inf")
    evaluated: int = 0
    trial_rows: List[Dict[str, Any]] = field(default_factory=list)


def _optimization_response(
    *,
    answer: str,
    params: Optional[Dict[str, Any]] = None,
    backtest_result: Optional[Dict[str, Any]] = None,
    analysis_result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "answer": answer,
        "params": params,
        "backtest_result": backtest_result,
        "analysis_result": analysis_result,
        "error": error,
    }


def _compute_base_summary(
    *,
    base_params: BacktestParams,
    run_backtest_advanced_service_fn: Callable[[AdvancedBacktestParams], Dict[str, Any]],
    optimization_train_ratio: float,
    optimization_monte_carlo_runs: int,
    log: logging.Logger,
) -> Dict[str, Any]:
    try:
        base_advanced = run_backtest_advanced_service_fn(
            to_advanced_params(
                base_params,
                optimization_train_ratio=optimization_train_ratio,
                optimization_monte_carlo_runs=optimization_monte_carlo_runs,
            )
        )
        if isinstance(base_advanced, dict) and base_advanced.get("success"):
            base_focus_summary = extract_advanced_summary(base_advanced, "out_of_sample")
            if not base_focus_summary:
                base_focus_summary = extract_advanced_summary(base_advanced, "full")
            if base_focus_summary:
                return base_focus_summary
    except Exception:
        log.exception("Failed to compute base optimization summary. Fallback baseline will be used.")
    return {}


def _record_trial(
    *,
    state: OptimizationSearchState,
    candidate: BacktestParams,
    advanced_result: Dict[str, Any],
    focus_summary: Dict[str, Any],
) -> None:
    score = score_advanced_backtest(advanced_result)
    if score == float("-inf"):
        return

    oos_trades = int(focus_summary.get("n_trades") or 0)
    oos_total_pnl = (
        float(focus_summary.get("total_pnl"))
        if oos_trades > 0 and focus_summary.get("total_pnl") is not None
        else None
    )
    oos_win_rate = (
        float(focus_summary.get("win_rate"))
        if oos_trades > 0 and focus_summary.get("win_rate") is not None
        else None
    )

    state.evaluated += 1
    state.trial_rows.append(
        {
            "score": score,
            "params": candidate.model_dump(),
            "oos_total_pnl": oos_total_pnl,
            "oos_win_rate": oos_win_rate,
            "oos_trades": oos_trades,
        }
    )

    if score <= state.best_score:
        return

    state.best_score = score
    state.best_params = candidate
    state.best_advanced_result = advanced_result
    state.best_summary = focus_summary


def _evaluate_candidates(
    *,
    candidates: List[BacktestParams],
    run_backtest_advanced_service_fn: Callable[[AdvancedBacktestParams], Dict[str, Any]],
    optimization_train_ratio: float,
    optimization_monte_carlo_runs: int,
    log: logging.Logger,
) -> OptimizationSearchState:
    state = OptimizationSearchState()

    for idx, candidate in enumerate(candidates):
        try:
            advanced_result = run_backtest_advanced_service_fn(
                to_advanced_params(
                    candidate,
                    optimization_train_ratio=optimization_train_ratio,
                    optimization_monte_carlo_runs=optimization_monte_carlo_runs,
                )
            )
        except Exception:
            log.exception("Auto optimization trial failed unexpectedly (trial=%s)", idx + 1)
            continue

        if not isinstance(advanced_result, dict) or not advanced_result.get("success"):
            continue

        focus_summary = extract_advanced_summary(advanced_result, "out_of_sample")
        if not focus_summary:
            focus_summary = extract_advanced_summary(advanced_result, "full")
        if not focus_summary:
            continue

        _record_trial(
            state=state,
            candidate=candidate,
            advanced_result=advanced_result,
            focus_summary=focus_summary,
        )

    return state


def _resolve_best_result_payload(
    *,
    best_params: BacktestParams,
    best_advanced_result: Dict[str, Any],
    run_backtest_service_fn: Callable[[BacktestParams], Dict[str, Any]],
    log: logging.Logger,
) -> Dict[str, Any]:
    try:
        best_result = run_backtest_service_fn(best_params)
        if not isinstance(best_result, dict) or not best_result.get("success"):
            return build_ui_result_from_advanced_payload(best_advanced_result)
        return best_result
    except Exception:
        log.exception("Failed to build final best-result payload. Falling back to advanced payload view.")
        return build_ui_result_from_advanced_payload(best_advanced_result)


def run_backtest_parameter_optimization(
    base_params: BacktestParams,
    prompt: str,
    *,
    run_backtest_service_fn: Callable[[BacktestParams], Dict[str, Any]],
    run_backtest_advanced_service_fn: Callable[[AdvancedBacktestParams], Dict[str, Any]],
    optimization_trials: int,
    optimization_train_ratio: float,
    optimization_monte_carlo_runs: int,
    feature_labels: List[Tuple[str, str]],
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    log = logger or logging.getLogger(__name__)
    base_summary = _compute_base_summary(
        base_params=base_params,
        run_backtest_advanced_service_fn=run_backtest_advanced_service_fn,
        optimization_train_ratio=optimization_train_ratio,
        optimization_monte_carlo_runs=optimization_monte_carlo_runs,
        log=log,
    )
    candidates = generate_optimization_candidates(
        base_params=base_params,
        prompt=prompt,
        optimization_trials=optimization_trials,
    )
    state = _evaluate_candidates(
        candidates=candidates,
        run_backtest_advanced_service_fn=run_backtest_advanced_service_fn,
        optimization_train_ratio=optimization_train_ratio,
        optimization_monte_carlo_runs=optimization_monte_carlo_runs,
        log=log,
    )
    state.base_summary = base_summary

    if state.best_params is None or state.best_advanced_result is None:
        return _optimization_response(
            answer="Auto optimization failed: no valid backtest trials were produced.",
            error="No valid optimization trial result.",
        )

    if not state.base_summary:
        state.base_summary = state.best_summary

    summary_text = format_optimization_summary(
        prompt=prompt,
        base_summary=state.base_summary,
        best_summary=state.best_summary,
        evaluated_count=state.evaluated,
        best_params=state.best_params,
    )
    characteristics = build_optimization_characteristics(
        state.trial_rows,
        prompt,
        feature_labels=feature_labels,
    )
    best_result = _resolve_best_result_payload(
        best_params=state.best_params,
        best_advanced_result=state.best_advanced_result,
        run_backtest_service_fn=run_backtest_service_fn,
        log=log,
    )

    return _optimization_response(
        answer=summary_text,
        params=state.best_params.model_dump(),
        backtest_result=best_result,
        analysis_result=characteristics,
    )


__all__ = ["run_backtest_parameter_optimization"]
