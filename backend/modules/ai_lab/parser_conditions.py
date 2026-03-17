"""Condition-specific parsers for AI lab prompts."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .parser_basics import _parse_operator_from_keyword
from .parser_constants import (
    BOLLINGER_CROSS_TOKENS,
    BOLLINGER_INTENT_PATTERN,
    BOLLINGER_RELATION_ABOVE_TOKENS,
    BOLLINGER_RELATION_BELOW_TOKENS,
    NUMERIC_INDICATOR_DEFS,
    STOCH_DEAD_TOKENS,
    STOCH_GOLDEN_TOKENS,
    STOCH_INTENT_TOKENS,
)


def _parse_numeric_indicator_conditions(prompt: str) -> List[Dict[str, Any]]:
    lowered = prompt.lower()
    results: List[Dict[str, Any]] = []
    dedup = set()

    for definition in NUMERIC_INDICATOR_DEFS:
        alias_pattern = "(?:" + "|".join(re.escape(alias) for alias in definition["aliases"]) + ")"

        explicit_pattern = re.compile(
            rf"{alias_pattern}\s*(?:값|value)?\s*(?:가|이|는|은)?\s*(>=|<=|>|<|=|==)\s*(-?\d+(?:\.\d+)?)",
            re.IGNORECASE,
        )
        keyword_pattern = re.compile(
            rf"{alias_pattern}\s*(?:값|value)?\s*(?:가|이|는|은)?\s*(-?\d+(?:\.\d+)?)\s*(이상|이하|초과|미만|above|below|over|under|greater|less)",
            re.IGNORECASE,
        )
        decade_pattern = re.compile(
            rf"{alias_pattern}\s*(?:값|value)?\s*(?:가|이|는|은)?\s*(\d{{1,3}})\s*대",
            re.IGNORECASE,
        )

        for match in explicit_pattern.finditer(prompt):
            op = match.group(1).replace("==", "=")
            threshold = float(match.group(2))
            dedup_key = (definition["key"], op, threshold)
            if dedup_key in dedup:
                continue
            dedup.add(dedup_key)
            results.append(
                {
                    "indicator": definition["key"],
                    "display": definition["display"],
                    "columns": definition["columns"],
                    "operator": op,
                    "threshold": threshold,
                    "span": match.span(),
                }
            )

        for match in keyword_pattern.finditer(prompt):
            threshold = float(match.group(1))
            op = _parse_operator_from_keyword(match.group(2), threshold)
            dedup_key = (definition["key"], op, threshold)
            if dedup_key in dedup:
                continue
            dedup.add(dedup_key)
            results.append(
                {
                    "indicator": definition["key"],
                    "display": definition["display"],
                    "columns": definition["columns"],
                    "operator": op,
                    "threshold": threshold,
                    "span": match.span(),
                }
            )

        for match in decade_pattern.finditer(prompt):
            lower_bound = float(match.group(1))
            upper_bound = lower_bound + 10.0
            for op, threshold in ((">=", lower_bound), ("<", upper_bound)):
                dedup_key = (definition["key"], op, threshold)
                if dedup_key in dedup:
                    continue
                dedup.add(dedup_key)
                results.append(
                    {
                        "indicator": definition["key"],
                        "display": definition["display"],
                        "columns": definition["columns"],
                        "operator": op,
                        "threshold": threshold,
                        "span": match.span(),
                    }
                )

        for alias in definition["aliases"]:
            if alias.lower() not in lowered:
                continue
            fallback_match = re.search(
                rf"{re.escape(alias)}\s*(?:is|was|=)?\s*(above|below|over|under|greater|less)\s*(-?\d+(?:\.\d+)?)",
                lowered,
            )
            if not fallback_match:
                continue
            threshold = float(fallback_match.group(2))
            op = _parse_operator_from_keyword(fallback_match.group(1), threshold)
            dedup_key = (definition["key"], op, threshold)
            if dedup_key in dedup:
                continue
            dedup.add(dedup_key)
            results.append(
                {
                    "indicator": definition["key"],
                    "display": definition["display"],
                    "columns": definition["columns"],
                    "operator": op,
                    "threshold": threshold,
                    "span": fallback_match.span(),
                }
            )

    return results


def _parse_bollinger_band_condition(prompt: str) -> Optional[Dict[str, Any]]:
    text = prompt or ""
    lowered = text.lower()
    if not BOLLINGER_INTENT_PATTERN.search(text):
        return None

    band = None
    if re.search(r"상단|upper", lowered):
        band = "upper"
    elif re.search(r"하단|lower", lowered):
        band = "lower"
    elif re.search(r"중단|중앙|middle|mid", lowered):
        band = "mid"
    if band is None:
        return None

    has_cross = any(token in lowered for token in BOLLINGER_CROSS_TOKENS)
    has_above = any(token in lowered for token in BOLLINGER_RELATION_ABOVE_TOKENS)
    has_below = any(token in lowered for token in BOLLINGER_RELATION_BELOW_TOKENS)

    if band == "upper":
        if has_cross:
            operator = "cross_above"
        elif has_below:
            operator = "below"
        else:
            operator = "above"
        columns = ["BB_Up", "BB_upper", "bb_up", "bb_upper"]
    elif band == "lower":
        if has_cross:
            operator = "cross_below"
        elif has_above:
            operator = "above"
        else:
            operator = "below"
        columns = ["BB_Low", "BB_lower", "bb_low", "bb_lower"]
    else:
        operator = "below" if has_below else "above"
        columns = ["BB_Mid", "BB_mid", "bb_mid"]

    span_match = re.search(
        r"(?:볼린저\s*밴드|볼밴|bollinger(?:\s*band)?|(?<![A-Za-z0-9])bb(?![A-Za-z0-9])).{0,30}"
        r"(?:상단|하단|중단|중앙|upper|lower|middle|mid)",
        text,
        re.IGNORECASE,
    )
    if not span_match:
        span_match = re.search(
            r"(?:상단|하단|중단|중앙|upper|lower|middle|mid).{0,30}"
            r"(?:볼린저\s*밴드|볼밴|bollinger(?:\s*band)?|(?<![A-Za-z0-9])bb(?![A-Za-z0-9]))",
            text,
            re.IGNORECASE,
        )

    return {
        "type": "bollinger_band",
        "band": band,
        "operator": operator,
        "columns": columns,
        "span": span_match.span() if span_match else None,
    }


def _detect_stoch_pair(prompt: str) -> tuple[str, str, str]:
    lower = prompt.lower()
    if (
        "20-12-12" in lower
        or "1스토" in prompt
        or "1번 스토" in prompt
        or "section 1" in lower
    ):
        return "slow_stoch_20k", "slow_stoch_20d", "20-12-12"
    if (
        "10-6-6" in lower
        or "2스토" in prompt
        or "2번 스토" in prompt
        or "section 2" in lower
    ):
        return "slow_stoch_10k", "slow_stoch_10d", "10-6-6"
    if (
        "5-3-3" in lower
        or "3스토" in prompt
        or "533스토" in prompt
        or "section 3" in lower
    ):
        return "slow_stoch_5k", "slow_stoch_5d", "5-3-3"
    return "slow_stoch_5k", "slow_stoch_5d", "5-3-3"


def _contains_stochastic_intent(prompt: str) -> bool:
    lower = (prompt or "").lower()
    if any(token in lower for token in STOCH_INTENT_TOKENS):
        return True
    return bool(
        re.search(
            r"(?:^|[^0-9a-zA-Z])(?:\d+\s*스토|533\s*스토)(?:$|[^0-9a-zA-Z])",
            prompt or "",
            re.IGNORECASE,
        )
    )


def _parse_stochastic_cross_condition(prompt: str) -> Optional[Dict[str, Any]]:
    lower = prompt.lower()
    if not _contains_stochastic_intent(prompt):
        return None

    if any(token in lower for token in STOCH_GOLDEN_TOKENS):
        cross_type = "golden"
        cross_match = re.search(
            r"골든\s*크로스|골드\s*크로스|골크|golden[\s-]*cross|gold[\s-]*cross|cross\s*up",
            prompt,
            re.IGNORECASE,
        )
    elif any(token in lower for token in STOCH_DEAD_TOKENS):
        cross_type = "dead"
        cross_match = re.search(
            r"데드크로스|데크|dead\s*cross|cross\s*down",
            prompt,
            re.IGNORECASE,
        )
    else:
        return None

    stoch_match = re.search(
        r"stoch(?:astic)?|스토캐스틱|스토캐|슬로우\s*스토캐스틱|slow\s*stochastic|3\s*스토|533\s*스토",
        prompt,
        re.IGNORECASE,
    )
    span = None
    if cross_match and stoch_match:
        span = (min(cross_match.start(), stoch_match.start()), max(cross_match.end(), stoch_match.end()))
    elif cross_match:
        span = cross_match.span()
    elif stoch_match:
        span = stoch_match.span()

    k_col, d_col, label = _detect_stoch_pair(prompt)
    return {
        "type": cross_type,
        "k_col": k_col,
        "d_col": d_col,
        "label": label,
        "span": span,
    }


def _map_candle_side(token: str) -> Optional[str]:
    normalized = token.strip().lower()
    if normalized in {"양봉", "bull", "bullish", "green", "상승"}:
        return "bull"
    if normalized in {"음봉", "bear", "bearish", "red", "하락"}:
        return "bear"
    return None


def _parse_streak_condition(prompt: str) -> Optional[Dict[str, Any]]:
    lowered = prompt.lower()
    patterns = [
        re.compile(r"(\d+)\s*(?:일|봉|캔들|bar|bars|day|days)?\s*연속\s*(양봉|음봉|bullish|bearish|green|red)", re.IGNORECASE),
        re.compile(r"(양봉|음봉|bullish|bearish|green|red)\s*(\d+)\s*(?:연속|in a row|consecutive)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(prompt)
        if not match:
            continue
        if match.group(1).isdigit():
            streak_len = max(1, int(match.group(1)))
            side = _map_candle_side(match.group(2)) or "bull"
        else:
            side = _map_candle_side(match.group(1)) or "bull"
            streak_len = max(1, int(match.group(2)))
        return {"streak_len": streak_len, "streak_side": side, "span": match.span()}

    if "연속" in prompt or "consecutive" in lowered or "in a row" in lowered:
        rough_match = re.search(r".{0,12}(?:연속|consecutive|in a row).{0,12}", prompt, re.IGNORECASE)
        if "음봉" in prompt or "bear" in lowered or "red" in lowered:
            return {"streak_len": 2, "streak_side": "bear", "span": rough_match.span() if rough_match else None}
        return {"streak_len": 2, "streak_side": "bull", "span": rough_match.span() if rough_match else None}

    return None


def _parse_next_candle_target(prompt: str, fallback_side: Optional[str]) -> str:
    next_match = re.search(
        r"(?:다음(?:날|봉|캔들)?|next(?:\s*(?:day|bar|candle))?).{0,8}?(양봉|음봉|bullish|bearish|green|red)",
        prompt,
        re.IGNORECASE,
    )
    if next_match:
        mapped = _map_candle_side(next_match.group(1))
        if mapped:
            return mapped
    if fallback_side:
        return fallback_side
    if "음봉" in prompt or "bear" in prompt.lower() or "red" in prompt.lower():
        return "bear"
    return "bull"


def _parse_macd_hist_condition(prompt: str) -> Optional[Dict[str, Any]]:
    match = re.search(
        r"macd(?:\s*[-_ ]?(?:hist(?:ogram)?|히스토그램|히스토))?\s*(?:값|value)?\s*(?:가|이|는|은)?\s*(>=|<=|>|<|=|==)?\s*(-?\d+(?:\.\d+)?)",
        prompt,
        re.IGNORECASE,
    )
    if not match:
        return None

    operator = (match.group(1) or "").strip()
    value = float(match.group(2))

    if not operator:
        lowered = prompt.lower()
        if any(token in lowered for token in ("이하", "below", "less", "under")):
            operator = "<="
        elif any(token in lowered for token in ("이상", "above", "greater", "over")):
            operator = ">="
        else:
            operator = ">=" if value >= 0 else "<="
    if operator == "==":
        operator = "="
    return {
        "operator": operator,
        "threshold": value,
        "span": match.span(),
    }


__all__ = [
    "_parse_numeric_indicator_conditions",
    "_parse_bollinger_band_condition",
    "_detect_stoch_pair",
    "_contains_stochastic_intent",
    "_parse_stochastic_cross_condition",
    "_map_candle_side",
    "_parse_streak_condition",
    "_parse_next_candle_target",
    "_parse_macd_hist_condition",
]
