"""Backtest parameter normalization helpers for AI lab service."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Sequence, Set

LEVERAGE_PATTERN = re.compile(
    r"(?:레버리지|leverage)\s*[:=]?\s*(\d{1,3})(?:\s*[xX배])?",
    re.IGNORECASE,
)

STRATEGY_ALIAS_MAP = {
    "connor": "Connors",
    "connors": "Connors",
    "squeeze": "Sqz",
    "sqz": "Sqz",
    "turtle": "Turtle",
    "mr": "MR",
    "meanreversion": "MR",
    "mean reversion": "MR",
    "rsi": "RSI",
    "ma": "MA",
    "movingaverage": "MA",
    "moving average": "MA",
    "bb": "BB",
    "bollinger": "BB",
    "engulf": "Engulf",
    "engulfing": "Engulf",
}


def is_missing_value(value: Any, missing_value_tokens: Set[str]) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        token = value.strip().lower()
        return token in missing_value_tokens
    return False


def normalize_leverage(value: Any, default: int = 1) -> int:
    if value is None:
        return default
    try:
        if isinstance(value, str):
            token = value.strip().lower().replace("x", "").replace("배", "").strip()
            parsed = int(float(token))
        elif isinstance(value, (int, float)):
            parsed = int(float(value))
        else:
            return default
    except (TypeError, ValueError):
        return default
    return max(1, min(125, parsed))


def extract_leverage_from_prompt(prompt: str) -> Optional[int]:
    match = LEVERAGE_PATTERN.search(prompt or "")
    if not match:
        return None
    try:
        value = int(match.group(1))
    except ValueError:
        return None
    return max(1, min(125, value))


def normalize_coin(value: Any, *, default: str, missing_value_tokens: Set[str]) -> str:
    if is_missing_value(value, missing_value_tokens):
        return default
    if not isinstance(value, str):
        return default

    coin = value.strip().upper()
    for suffix in ("/USDT", "-USDT", "_USDT", "USDT"):
        if coin.endswith(suffix):
            coin = coin[: -len(suffix)]
            break

    coin = "".join(ch for ch in coin if ch.isalnum())
    if not (2 <= len(coin) <= 20):
        return default
    return coin


def normalize_interval(
    value: Any,
    *,
    default: str,
    missing_value_tokens: Set[str],
    valid_backtest_intervals: Set[str],
    interval_aliases: Dict[str, str],
    lowercase_backtest_intervals: Set[str],
) -> str:
    if is_missing_value(value, missing_value_tokens):
        return default
    if not isinstance(value, str):
        return default

    interval = value.strip()
    lowered = interval.lower()

    if interval in valid_backtest_intervals:
        return interval
    if lowered in interval_aliases:
        return interval_aliases[lowered]
    if lowered in lowercase_backtest_intervals:
        return lowered
    return default


def normalize_direction(value: Any, *, default: str, missing_value_tokens: Set[str]) -> str:
    if is_missing_value(value, missing_value_tokens):
        return default
    if not isinstance(value, str):
        return default

    token = value.strip().lower()
    long_tokens = {"long", "buy", "bull", "up", "롱", "매수"}
    short_tokens = {"short", "sell", "bear", "down", "숏", "매도"}

    if token in long_tokens:
        return "Long"
    if token in short_tokens:
        return "Short"
    return default


def normalize_strategy_id(
    value: Any,
    *,
    default: str,
    missing_value_tokens: Set[str],
    strategy_ids: Sequence[str],
) -> str:
    valid_ids = [str(item) for item in strategy_ids]
    valid_id_set = set(valid_ids)
    normalized_index = {sid.lower(): sid for sid in valid_ids}

    fallback = default if default in valid_id_set else valid_ids[0]
    if is_missing_value(value, missing_value_tokens):
        return fallback
    if not isinstance(value, str):
        return fallback

    token = value.strip()
    if token in valid_id_set:
        return token

    lowered = token.lower()
    if lowered in STRATEGY_ALIAS_MAP and STRATEGY_ALIAS_MAP[lowered] in valid_id_set:
        return STRATEGY_ALIAS_MAP[lowered]
    if lowered in normalized_index:
        return normalized_index[lowered]
    return fallback


def sanitize_backtest_params(
    raw_params: Any,
    *,
    missing_value_tokens: Set[str],
    valid_backtest_intervals: Set[str],
    interval_aliases: Dict[str, str],
    lowercase_backtest_intervals: Set[str],
    strategy_ids: Sequence[str],
    default_coin: str = "BTC",
    default_interval: str = "4h",
    default_strategy_id: str = "RSI",
    default_direction: str = "Long",
) -> Dict[str, Any]:
    params = dict(raw_params) if isinstance(raw_params, dict) else {}
    sanitized = dict(params)
    sanitized["coin"] = normalize_coin(
        params.get("coin"),
        default=default_coin,
        missing_value_tokens=missing_value_tokens,
    )
    sanitized["interval"] = normalize_interval(
        params.get("interval"),
        default=default_interval,
        missing_value_tokens=missing_value_tokens,
        valid_backtest_intervals=valid_backtest_intervals,
        interval_aliases=interval_aliases,
        lowercase_backtest_intervals=lowercase_backtest_intervals,
    )
    sanitized["strategy_id"] = normalize_strategy_id(
        params.get("strategy_id"),
        default=default_strategy_id,
        missing_value_tokens=missing_value_tokens,
        strategy_ids=strategy_ids,
    )
    sanitized["direction"] = normalize_direction(
        params.get("direction"),
        default=default_direction,
        missing_value_tokens=missing_value_tokens,
    )
    sanitized["leverage"] = normalize_leverage(params.get("leverage"), default=1)
    sanitized["use_csv"] = True
    return sanitized


def minimal_backtest_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "coin": params["coin"],
        "interval": params["interval"],
        "strategy_id": params["strategy_id"],
        "direction": params["direction"],
        "leverage": normalize_leverage(params.get("leverage"), default=1),
        "use_csv": True,
    }
