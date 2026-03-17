"""Prompt parsing and conditional probability analysis helpers for AI lab."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd

from .analyzer_conditions import build_probability_condition_specs
from .analyzer_formatting import _append_ignored_conditions_note, _format_probability_answer
from .analyzer_result import build_probability_analysis_result, calculate_probability_summary
from .expression import _evaluate_condition_expression
from .parser import (
    infer_interval_from_prompt,
    normalize_coin_from_text,
    contains_probability_intent,
    _parse_numeric_indicator_conditions,
    _parse_bollinger_band_condition,
    _parse_stochastic_cross_condition,
    _parse_streak_condition,
    _parse_next_candle_target,
    _parse_macd_hist_condition,
)


def _probability_response(
    *,
    answer: str,
    analysis_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "answer": answer,
        "backtest_params": None,
        "backtest_result": None,
        "analysis_result": analysis_result,
        "error": None,
    }


def run_conditional_probability_analysis(
    prompt: str,
    ui_context: Dict[str, str],
    *,
    load_data_for_analysis_fn: Callable[..., Tuple[pd.DataFrame, str]],
    prepare_strategy_data_fn: Callable[..., pd.DataFrame],
    compute_trend_judgment_indicators_fn: Callable[..., pd.DataFrame],
    normalize_interval_fn: Callable[..., str],
    calculate_binomial_pvalue_fn: Callable[..., Any],
    wilson_confidence_interval_fn: Callable[..., Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not contains_probability_intent(prompt):
        return None

    coin = normalize_coin_from_text(ui_context.get("coin"), fallback="BTC")
    interval = normalize_interval_fn(
        infer_interval_from_prompt(prompt, ui_context.get("interval", "4h")),
        default="4h",
    )
    streak_condition = _parse_streak_condition(prompt)
    target_side = _parse_next_candle_target(
        prompt,
        fallback_side=streak_condition["streak_side"] if streak_condition else None,
    )
    macd_condition = _parse_macd_hist_condition(prompt)
    numeric_conditions = _parse_numeric_indicator_conditions(prompt)
    bollinger_condition = _parse_bollinger_band_condition(prompt)
    stoch_condition = _parse_stochastic_cross_condition(prompt)

    df, source = load_data_for_analysis_fn(coin, interval, use_csv=True, total_candles=3000)
    prepared = prepare_strategy_data_fn(df.copy())
    prepared = compute_trend_judgment_indicators_fn(prepared.copy())
    if prepared is None or prepared.empty:
        return _probability_response(answer=f"[조건부 확률 분석] {coin} {interval}: 데이터가 비어 있습니다.")

    is_bull = prepared["close"] > prepared["open"]
    is_bear = prepared["close"] < prepared["open"]
    target_series = is_bull if target_side == "bull" else is_bear

    condition_bundle = build_probability_condition_specs(
        prompt=prompt,
        prepared=prepared,
        streak_condition=streak_condition,
        macd_condition=macd_condition,
        numeric_conditions=numeric_conditions,
        bollinger_condition=bollinger_condition,
        stoch_condition=stoch_condition,
    )
    if condition_bundle["error_message"]:
        return _probability_response(
            answer=f"[조건부 확률 분석] {coin} {interval}: {condition_bundle['error_message']}"
        )

    condition_specs = condition_bundle["condition_specs"]
    ignored_conditions = condition_bundle["ignored_conditions"]

    mask, expression_tokens, condition_text = _evaluate_condition_expression(
        prompt=prompt,
        condition_specs=condition_specs,
        index=prepared.index,
    )

    summary = calculate_probability_summary(
        mask=mask,
        target_series=target_series,
        calculate_binomial_pvalue_fn=calculate_binomial_pvalue_fn,
        wilson_confidence_interval_fn=wilson_confidence_interval_fn,
    )

    is_ko = bool(re.search(r"[가-힣]", prompt or ""))
    answer = _format_probability_answer(
        coin=coin,
        interval=interval,
        source=source,
        target_side=target_side,
        condition_text=condition_text,
        sample_count=summary["sample_count"],
        success_count=summary["success_count"],
        probability_rate=summary["probability_rate"],
        ci_lower=summary["ci_lower"],
        ci_upper=summary["ci_upper"],
        p_value=summary["p_value"],
        reliability=summary["reliability"],
        gati_index=summary["gati_index"],
        is_ko=is_ko,
    )
    answer = _append_ignored_conditions_note(answer, prompt, ignored_conditions)

    analysis_result = build_probability_analysis_result(
        coin=coin,
        interval=interval,
        source=source,
        target_side=target_side,
        condition_text=condition_text,
        condition_specs=condition_specs,
        ignored_conditions=ignored_conditions,
        expression_tokens=expression_tokens,
        summary=summary,
    )

    return _probability_response(answer=answer, analysis_result=analysis_result)
