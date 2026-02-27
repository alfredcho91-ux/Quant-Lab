"""Prompt parsing and conditional probability analysis helpers for AI lab."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from .expression import (
    _resolve_indicator_column,
    _apply_comparator,
    _coerce_mask,
    _sorted_condition_specs,
    _build_expression_tokens,
    _insert_implicit_and,
    _infix_to_postfix,
    _eval_postfix_mask,
    _format_expression_tokens,
    _evaluate_condition_expression,
)
from .stats_math import (
    _calculate_gati_index,
    _p_value_reliability_label,
    _reliability_label,
    _safe_float,
)
from .parser import (
    CONTEXT_LINE_PATTERN,
    INTERVAL_ALIASES,
    MONTH_INTERVAL_PATTERNS,
    INTERVAL_REGEX_PATTERNS,
    INTERVAL_ALIAS_REGEX_PATTERNS,
    KOR_INTERVAL_HINTS,
    COMPARATOR_KEYWORD_TO_OP,
    NUMERIC_INDICATOR_DEFS,
    STOCH_GOLDEN_TOKENS,
    STOCH_DEAD_TOKENS,
    STOCH_INTENT_TOKENS,
    OPTIMIZATION_HINT_TOKENS,
    split_prompt_and_ui_context,
    infer_interval_from_prompt,
    normalize_coin_from_text,
    contains_probability_intent,
    looks_like_optimization_request,
    _parse_operator_from_keyword,
    _parse_numeric_indicator_conditions,
    _detect_stoch_pair,
    _contains_stochastic_intent,
    _parse_stochastic_cross_condition,
    _map_candle_side,
    _parse_streak_condition,
    _parse_next_candle_target,
    _parse_macd_hist_condition,
    _normalize_expression_text,
)


def _format_probability_answer(
    *,
    coin: str,
    interval: str,
    source: str,
    target_side: str,
    condition_text: str,
    sample_count: int,
    success_count: int,
    probability_rate: Optional[float],
    ci_lower: Optional[float],
    ci_upper: Optional[float],
    p_value: Optional[float],
    reliability: str,
    gati_index: float,
) -> str:
    target_label = "양봉" if target_side == "bull" else "음봉"

    if sample_count == 0 or probability_rate is None:
        return (
            f"[조건부 확률 분석] {coin} {interval} (source={source})\n"
            f"조건: {condition_text}\n"
            "조건을 만족하는 표본이 없어 확률을 계산할 수 없습니다."
        )

    ci_text = (
        f"{ci_lower:.2f}% ~ {ci_upper:.2f}%"
        if ci_lower is not None and ci_upper is not None
        else "N/A"
    )
    p_text = f"{p_value:.4f}" if p_value is not None else "N/A"
    p_reliability = _p_value_reliability_label(p_value)
    return (
        f"[조건부 확률 분석] {coin} {interval} (source={source})\n"
        f"조건: {condition_text}\n"
        f"결과: 다음 봉 {target_label} 확률 {probability_rate:.2f}% "
        f"(성공 {success_count} / 표본 {sample_count})\n"
        f"95% Wilson CI: {ci_text}\n"
        f"통계 신뢰도(p-value): {p_reliability} (p={p_text}, vs 50%)\n"
        f"신뢰도: {reliability}\n"
        f"GATI Index: {gati_index:.2f}/100"
    )


def _append_ignored_conditions_note(answer: str, prompt: str, ignored_conditions: List[str]) -> str:
    unique_conditions = [item for item in dict.fromkeys(ignored_conditions) if item]
    if not unique_conditions:
        return answer

    detail = ", ".join(unique_conditions)
    if re.search(r"[가-힣]", prompt or ""):
        return f"{answer}\n주의: 일부 조건은 파싱/데이터 한계로 제외됨 -> {detail}"
    return f"{answer}\nNote: Some conditions were excluded due to parsing/data limits -> {detail}"


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
    stoch_condition = _parse_stochastic_cross_condition(prompt)

    df, source = load_data_for_analysis_fn(coin, interval, use_csv=True, total_candles=3000)
    prepared = prepare_strategy_data_fn(df.copy())
    prepared = compute_trend_judgment_indicators_fn(prepared.copy())
    if prepared is None or prepared.empty:
        return {
            "answer": f"[조건부 확률 분석] {coin} {interval}: 데이터가 비어 있습니다.",
            "backtest_params": None,
            "backtest_result": None,
            "analysis_result": None,
            "error": None,
        }

    is_bull = prepared["close"] > prepared["open"]
    is_bear = prepared["close"] < prepared["open"]
    target_series = is_bull if target_side == "bull" else is_bear

    condition_specs: List[Dict[str, Any]] = []
    ignored_conditions: List[str] = []

    if streak_condition:
        streak_len = int(streak_condition["streak_len"])
        streak_side = str(streak_condition["streak_side"])
        streak_series = is_bull if streak_side == "bull" else is_bear
        streak_mask = pd.Series(True, index=prepared.index)
        for offset in range(streak_len):
            streak_mask &= streak_series.shift(offset, fill_value=False)
        streak_label = "양봉" if streak_side == "bull" else "음봉"
        label = f"{streak_len}연속 {streak_label}"
        component = {
            "type": "streak",
            "streak_len": streak_len,
            "streak_side": streak_side,
        }
        condition_specs.append(
            {
                "order": len(condition_specs),
                "label": label,
                "mask": _coerce_mask(streak_mask),
                "component": component,
                "span": streak_condition.get("span"),
            }
        )

    if macd_condition is not None:
        macd_op = str(macd_condition["operator"])
        macd_threshold = float(macd_condition["threshold"])
        macd_col = "MACD_hist" if "MACD_hist" in prepared.columns else "macd_hist"
        if macd_col not in prepared.columns:
            return {
                "answer": f"[조건부 확률 분석] {coin} {interval}: MACD histogram 컬럼이 없어 계산할 수 없습니다.",
                "backtest_params": None,
                "backtest_result": None,
                "analysis_result": None,
                "error": None,
            }
        label = f"MACD 히스토 {macd_op} {macd_threshold:g}"
        component = {
            "type": "numeric_indicator",
            "indicator": "macd_hist",
            "column": macd_col,
            "operator": macd_op,
            "threshold": macd_threshold,
        }
        condition_specs.append(
            {
                "order": len(condition_specs),
                "label": label,
                "mask": _coerce_mask(_apply_comparator(prepared[macd_col], macd_op, macd_threshold)),
                "component": component,
                "span": macd_condition.get("span"),
            }
        )

    for numeric_cond in numeric_conditions:
        col = _resolve_indicator_column(prepared, numeric_cond["columns"])
        if col is None:
            ignored_conditions.append(f"{numeric_cond['display']} {numeric_cond['operator']} {numeric_cond['threshold']:g}")
            continue
        label = f"{numeric_cond['display']} {numeric_cond['operator']} {numeric_cond['threshold']:g}"
        component = {
            "type": "numeric_indicator",
            "indicator": numeric_cond["indicator"],
            "column": col,
            "operator": numeric_cond["operator"],
            "threshold": numeric_cond["threshold"],
        }
        condition_specs.append(
            {
                "order": len(condition_specs),
                "label": label,
                "mask": _coerce_mask(
                    _apply_comparator(
                        prepared[col],
                        numeric_cond["operator"],
                        numeric_cond["threshold"],
                    )
                ),
                "component": component,
                "span": numeric_cond.get("span"),
            }
        )

    if stoch_condition:
        k_col = stoch_condition["k_col"]
        d_col = stoch_condition["d_col"]
        cross_type = stoch_condition["type"]
        if k_col in prepared.columns and d_col in prepared.columns:
            if cross_type == "golden":
                stoch_mask = (prepared[k_col] > prepared[d_col]) & (
                    prepared[k_col].shift(1) <= prepared[d_col].shift(1)
                )
                label = f"스토캐({stoch_condition['label']}) 골든크로스"
            else:
                stoch_mask = (prepared[k_col] < prepared[d_col]) & (
                    prepared[k_col].shift(1) >= prepared[d_col].shift(1)
                )
                label = f"스토캐({stoch_condition['label']}) 데드크로스"

            component = {
                "type": "stochastic_cross",
                "cross_type": cross_type,
                "k_column": k_col,
                "d_column": d_col,
                "stoch_label": stoch_condition["label"],
            }
            condition_specs.append(
                {
                    "order": len(condition_specs),
                    "label": label,
                    "mask": _coerce_mask(stoch_mask),
                    "component": component,
                    "span": stoch_condition.get("span"),
                }
            )
        else:
            ignored_conditions.append(f"스토캐({stoch_condition['label']}) {cross_type} cross")
    elif _contains_stochastic_intent(prompt):
        ignored_conditions.append("스토캐 조건(크로스 타입 미인식)")

    mask, expression_tokens, condition_text = _evaluate_condition_expression(
        prompt=prompt,
        condition_specs=condition_specs,
        index=prepared.index,
    )

    next_target = target_series.shift(-1)
    valid_mask = mask & next_target.notna()
    sample_count = int(valid_mask.sum())
    success_count = int((valid_mask & (next_target == True)).sum())

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
    condition_components = [spec["component"] for spec in _sorted_condition_specs(condition_specs)]

    answer = _format_probability_answer(
        coin=coin,
        interval=interval,
        source=source,
        target_side=target_side,
        condition_text=condition_text,
        sample_count=sample_count,
        success_count=success_count,
        probability_rate=probability_rate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        reliability=reliability,
        gati_index=gati_index,
    )
    answer = _append_ignored_conditions_note(answer, prompt, ignored_conditions)

    failure_count = max(0, sample_count - success_count)
    success_rate = (success_count / sample_count * 100.0) if sample_count > 0 else 0.0
    failure_rate = 100.0 - success_rate if sample_count > 0 else 0.0
    analysis_result = {
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
        },
        "outcome_bars": [
            {
                "key": "success",
                "label": "Success",
                "count": success_count,
                "rate_pct": round(success_rate, 2),
            },
            {
                "key": "failure",
                "label": "Failure",
                "count": failure_count,
                "rate_pct": round(failure_rate, 2),
            },
        ],
        "confidence_band": {
            "baseline": 50.0,
            "center": _safe_float(probability_rate),
            "lower": ci_lower,
            "upper": ci_upper,
        },
        "generated_at": pd.Timestamp.utcnow().isoformat(),
    }

    return {
        "answer": answer,
        "backtest_params": None,
        "backtest_result": None,
        "analysis_result": analysis_result,
        "error": None,
    }
