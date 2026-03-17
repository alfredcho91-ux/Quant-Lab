"""Shared low-level helpers for AI lab prompt parsing."""

from __future__ import annotations

import re
from typing import Dict, Optional

from .parser_constants import (
    COMPARATOR_KEYWORD_TO_OP,
    CONTEXT_LINE_PATTERN,
    INTERVAL_ALIAS_REGEX_PATTERNS,
    INTERVAL_REGEX_PATTERNS,
    KOR_INTERVAL_HINTS,
    MONTH_INTERVAL_PATTERNS,
    OPTIMIZATION_HINT_TOKENS,
)


def split_prompt_and_ui_context(prompt: str) -> tuple[str, Dict[str, str]]:
    text = prompt or ""
    marker = "[UI_CONTEXT]"
    if marker not in text:
        return text.strip(), {}

    before, after = text.split(marker, 1)
    ctx: Dict[str, str] = {}
    for raw in after.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = CONTEXT_LINE_PATTERN.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        ctx[key] = value
    return before.strip(), ctx


def infer_interval_from_prompt(prompt: str, fallback: str) -> str:
    if not prompt:
        return fallback

    if any(pattern.search(prompt) for pattern in MONTH_INTERVAL_PATTERNS):
        return "1M"

    for pattern, interval in INTERVAL_REGEX_PATTERNS:
        if pattern.search(prompt):
            return interval

    for pattern, canonical in INTERVAL_ALIAS_REGEX_PATTERNS:
        if pattern.search(prompt):
            return canonical

    for keyword, interval in KOR_INTERVAL_HINTS:
        if keyword in prompt:
            return interval

    if re.search(r"\d+\s*일\s*연속", prompt):
        return "1d"
    return fallback


def normalize_coin_from_text(value: Optional[str], fallback: str = "BTC") -> str:
    if not value:
        return fallback
    symbol = value.strip().upper().replace("/USDT", "").replace("USDT", "")
    symbol = "".join(ch for ch in symbol if ch.isalnum())
    if 2 <= len(symbol) <= 20:
        return symbol
    return fallback


def contains_probability_intent(prompt: str) -> bool:
    lowered = prompt.lower()
    probability_tokens = ("확률", "probability", "가능성")
    candle_tokens = ("양봉", "음봉", "bull", "bear", "green", "red", "다음봉", "다음날", "next")
    return any(token in lowered for token in probability_tokens) and any(
        token in lowered for token in candle_tokens
    )


def looks_like_optimization_request(prompt: str) -> bool:
    lowered = (prompt or "").lower()
    return any(token in lowered for token in OPTIMIZATION_HINT_TOKENS)


def _parse_operator_from_keyword(keyword: str, fallback_value: float) -> str:
    normalized = keyword.strip().lower()
    for token, op in COMPARATOR_KEYWORD_TO_OP.items():
        if token in normalized:
            return op
    return ">=" if fallback_value >= 0 else "<="


def _normalize_expression_text(text: str) -> str:
    normalized = text
    replacements = [
        (r"\bAND\b", " AND "),
        (r"\bOR\b", " OR "),
        (r"\bNOT\b", " NOT "),
        (r"&&", " AND "),
        (r"\|\|", " OR "),
        (r"(?<![A-Z0-9_])and(?![A-Z0-9_])", " AND "),
        (r"(?<![A-Z0-9_])or(?![A-Z0-9_])", " OR "),
        (r"(?<![A-Z0-9_])not(?![A-Z0-9_])", " NOT "),
        (r"그리고|이며|이고|면서|및", " AND "),
        (r"또는|혹은|아니면", " OR "),
    ]
    for pattern, repl in replacements:
        normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
    return normalized


__all__ = [
    "split_prompt_and_ui_context",
    "infer_interval_from_prompt",
    "normalize_coin_from_text",
    "contains_probability_intent",
    "looks_like_optimization_request",
    "_parse_operator_from_keyword",
    "_normalize_expression_text",
]
