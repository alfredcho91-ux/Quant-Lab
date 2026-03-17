"""Condition-spec builders for AI lab conditional probability analysis."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .expression import _apply_comparator, _coerce_mask, _resolve_indicator_column
from .parser import _contains_stochastic_intent


def _is_korean_prompt(prompt: str) -> bool:
    return bool(re.search(r"[가-힣]", prompt or ""))


def _append_condition_spec(
    condition_specs: List[Dict[str, Any]],
    *,
    label: str,
    mask: pd.Series,
    component: Dict[str, Any],
    span: Optional[tuple[int, int]],
) -> None:
    condition_specs.append(
        {
            "order": len(condition_specs),
            "label": label,
            "mask": _coerce_mask(mask),
            "component": component,
            "span": span,
        }
    )


def _build_streak_condition_spec(
    prompt: str,
    prepared: pd.DataFrame,
    streak_condition: Dict[str, Any],
) -> Dict[str, Any]:
    is_bull = prepared["close"] > prepared["open"]
    is_bear = prepared["close"] < prepared["open"]
    streak_len = int(streak_condition["streak_len"])
    streak_side = str(streak_condition["streak_side"])
    streak_series = is_bull if streak_side == "bull" else is_bear
    streak_mask = pd.Series(True, index=prepared.index)
    for offset in range(streak_len):
        streak_mask &= streak_series.shift(offset, fill_value=False)

    if _is_korean_prompt(prompt):
        streak_label = "양봉" if streak_side == "bull" else "음봉"
        label = f"{streak_len}연속 {streak_label}"
    else:
        streak_label = "Bull" if streak_side == "bull" else "Bear"
        label = f"{streak_len} Consecutive {streak_label}"

    return {
        "label": label,
        "mask": streak_mask,
        "component": {
            "type": "streak",
            "streak_len": streak_len,
            "streak_side": streak_side,
        },
        "span": streak_condition.get("span"),
    }


def _build_macd_condition_spec(
    prompt: str,
    prepared: pd.DataFrame,
    macd_condition: Dict[str, Any],
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    macd_op = str(macd_condition["operator"])
    macd_threshold = float(macd_condition["threshold"])
    macd_col = "MACD_hist" if "MACD_hist" in prepared.columns else "macd_hist"
    if macd_col not in prepared.columns:
        return None, "MACD histogram 컬럼이 없어 계산할 수 없습니다."

    if _is_korean_prompt(prompt):
        label = f"MACD 히스토 {macd_op} {macd_threshold:g}"
    else:
        label = f"MACD Hist {macd_op} {macd_threshold:g}"

    return (
        {
            "label": label,
            "mask": _apply_comparator(prepared[macd_col], macd_op, macd_threshold),
            "component": {
                "type": "numeric_indicator",
                "indicator": "macd_hist",
                "column": macd_col,
                "operator": macd_op,
                "threshold": macd_threshold,
            },
            "span": macd_condition.get("span"),
        },
        None,
    )


def _build_numeric_condition_spec(
    prepared: pd.DataFrame,
    numeric_cond: Dict[str, Any],
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    col = _resolve_indicator_column(prepared, numeric_cond["columns"])
    if col is None:
        return None, f"{numeric_cond['display']} {numeric_cond['operator']} {numeric_cond['threshold']:g}"

    return (
        {
            "label": f"{numeric_cond['display']} {numeric_cond['operator']} {numeric_cond['threshold']:g}",
            "mask": _apply_comparator(
                prepared[col],
                numeric_cond["operator"],
                numeric_cond["threshold"],
            ),
            "component": {
                "type": "numeric_indicator",
                "indicator": numeric_cond["indicator"],
                "column": col,
                "operator": numeric_cond["operator"],
                "threshold": numeric_cond["threshold"],
            },
            "span": numeric_cond.get("span"),
        },
        None,
    )


def _build_bollinger_condition_spec(
    prompt: str,
    prepared: pd.DataFrame,
    bollinger_condition: Dict[str, Any],
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    band_col = _resolve_indicator_column(prepared, bollinger_condition["columns"])
    close_col = _resolve_indicator_column(prepared, ["close", "Close", "CLOSE"])
    if band_col is None or close_col is None:
        return None, "볼린저 밴드 조건"

    band_series = prepared[band_col]
    close_series = prepared[close_col]
    operator = str(bollinger_condition["operator"])
    band = str(bollinger_condition["band"])

    if operator == "cross_above":
        bb_mask = (close_series > band_series) & (close_series.shift(1) <= band_series.shift(1))
    elif operator == "cross_below":
        bb_mask = (close_series < band_series) & (close_series.shift(1) >= band_series.shift(1))
    elif operator == "below":
        bb_mask = close_series < band_series
    else:
        bb_mask = close_series > band_series

    if _is_korean_prompt(prompt):
        band_label = {"upper": "상단", "lower": "하단", "mid": "중단"}.get(band, band)
        operator_label = {
            "cross_above": "종가 돌파",
            "cross_below": "종가 이탈",
            "above": "위 마감",
            "below": "아래 마감",
        }.get(operator, operator)
        label = f"볼린저 {band_label} {operator_label}"
    else:
        band_label = {"upper": "Upper", "lower": "Lower", "mid": "Mid"}.get(band, band)
        operator_label = {
            "cross_above": "Cross Above",
            "cross_below": "Cross Below",
            "above": "Close Above",
            "below": "Close Below",
        }.get(operator, operator)
        label = f"BB {band_label} {operator_label}"

    return (
        {
            "label": label,
            "mask": bb_mask,
            "component": {
                "type": "bollinger_band",
                "band": band,
                "operator": operator,
                "column": band_col,
                "close_column": close_col,
            },
            "span": bollinger_condition.get("span"),
        },
        None,
    )


def _build_stochastic_condition_spec(
    prompt: str,
    prepared: pd.DataFrame,
    stoch_condition: Dict[str, Any],
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    k_col = stoch_condition["k_col"]
    d_col = stoch_condition["d_col"]
    cross_type = stoch_condition["type"]

    if k_col not in prepared.columns or d_col not in prepared.columns:
        if k_col.startswith("slow_stoch_") and d_col.startswith("slow_stoch_"):
            legacy_k = k_col.replace("slow_stoch_", "stoch_rsi_", 1)
            legacy_d = d_col.replace("slow_stoch_", "stoch_rsi_", 1)
            if legacy_k in prepared.columns and legacy_d in prepared.columns:
                k_col, d_col = legacy_k, legacy_d
        elif k_col.startswith("stoch_rsi_") and d_col.startswith("stoch_rsi_"):
            canonical_k = k_col.replace("stoch_rsi_", "slow_stoch_", 1)
            canonical_d = d_col.replace("stoch_rsi_", "slow_stoch_", 1)
            if canonical_k in prepared.columns and canonical_d in prepared.columns:
                k_col, d_col = canonical_k, canonical_d

    if k_col not in prepared.columns or d_col not in prepared.columns:
        return None, f"스토캐({stoch_condition['label']}) {cross_type} cross"

    is_ko = _is_korean_prompt(prompt)
    if cross_type == "golden":
        stoch_mask = (prepared[k_col] > prepared[d_col]) & (prepared[k_col].shift(1) <= prepared[d_col].shift(1))
        label = (
            f"스토캐({stoch_condition['label']}) 골든크로스"
            if is_ko
            else f"Stoch({stoch_condition['label']}) Golden Cross"
        )
    else:
        stoch_mask = (prepared[k_col] < prepared[d_col]) & (prepared[k_col].shift(1) >= prepared[d_col].shift(1))
        label = (
            f"스토캐({stoch_condition['label']}) 데드크로스"
            if is_ko
            else f"Stoch({stoch_condition['label']}) Dead Cross"
        )

    return (
        {
            "label": label,
            "mask": stoch_mask,
            "component": {
                "type": "stochastic_cross",
                "cross_type": cross_type,
                "k_column": k_col,
                "d_column": d_col,
                "stoch_label": stoch_condition["label"],
            },
            "span": stoch_condition.get("span"),
        },
        None,
    )


def build_probability_condition_specs(
    *,
    prompt: str,
    prepared: pd.DataFrame,
    streak_condition: Optional[Dict[str, Any]],
    macd_condition: Optional[Dict[str, Any]],
    numeric_conditions: List[Dict[str, Any]],
    bollinger_condition: Optional[Dict[str, Any]],
    stoch_condition: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    condition_specs: List[Dict[str, Any]] = []
    ignored_conditions: List[str] = []

    if streak_condition:
        streak_spec = _build_streak_condition_spec(prompt, prepared, streak_condition)
        _append_condition_spec(condition_specs, **streak_spec)

    if macd_condition is not None:
        macd_spec, macd_error = _build_macd_condition_spec(prompt, prepared, macd_condition)
        if macd_error:
            return {
                "condition_specs": condition_specs,
                "ignored_conditions": ignored_conditions,
                "error_message": macd_error,
            }
        _append_condition_spec(condition_specs, **macd_spec)

    for numeric_cond in numeric_conditions:
        numeric_spec, ignored_message = _build_numeric_condition_spec(prepared, numeric_cond)
        if ignored_message:
            ignored_conditions.append(ignored_message)
            continue
        _append_condition_spec(condition_specs, **numeric_spec)

    if bollinger_condition:
        bollinger_spec, ignored_message = _build_bollinger_condition_spec(prompt, prepared, bollinger_condition)
        if ignored_message:
            ignored_conditions.append(ignored_message)
        else:
            _append_condition_spec(condition_specs, **bollinger_spec)

    if stoch_condition:
        stochastic_spec, ignored_message = _build_stochastic_condition_spec(prompt, prepared, stoch_condition)
        if ignored_message:
            ignored_conditions.append(ignored_message)
        else:
            _append_condition_spec(condition_specs, **stochastic_spec)
    elif _contains_stochastic_intent(prompt):
        ignored_conditions.append("스토캐 조건(크로스 타입 미인식)")

    return {
        "condition_specs": condition_specs,
        "ignored_conditions": ignored_conditions,
        "error_message": None,
    }


__all__ = ["build_probability_condition_specs"]
