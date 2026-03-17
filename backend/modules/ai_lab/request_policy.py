"""Prompt ambiguity and clarification helpers for AI research."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, Optional


def looks_ambiguous_prompt(
    prompt: str,
    *,
    contains_probability_intent_fn: Callable[[str], bool],
    strategies: Iterable[Dict[str, Any]],
) -> bool:
    text = (prompt or "").strip()
    lowered = text.lower()
    if not text:
        return True
    if contains_probability_intent_fn(text):
        return False

    strategy_tokens = [str(item.get("id", "")).lower() for item in strategies if item.get("id")]
    indicator_tokens = (
        "rsi",
        "macd",
        "stoch",
        "스토캐",
        "스토캐스틱",
        "볼린저",
        "bb",
        "sma",
        "ema",
        "adx",
        "atr",
        "vwap",
        "supertrend",
        "골든크로스",
        "데드크로스",
    )
    has_strategy = any(token and token in lowered for token in strategy_tokens)
    has_indicator = any(token in lowered for token in indicator_tokens)
    has_threshold = bool(re.search(r"(>=|<=|>|<|=)\s*-?\d+|\d+\s*(?:일|봉|bars?)\s*연속", lowered))
    has_direction = any(token in lowered for token in ("long", "short", "롱", "숏", "매수", "매도"))

    generic_patterns = (
        r"돈\s*버",
        r"수익.*전략",
        r"좋은\s*전략",
        r"추천\s*전략",
        r"best\s*strategy",
        r"profit",
        r"아무거나",
    )
    has_generic_intent = any(re.search(pattern, lowered) for pattern in generic_patterns)

    if has_strategy or has_indicator or has_threshold:
        return False
    if len(text) <= 10:
        return True
    if has_generic_intent and not has_direction:
        return True
    return "백테스트" in text and not (has_strategy or has_indicator or has_threshold)


def build_clarification_payload(
    prompt: str,
    ui_context: Dict[str, str],
    *,
    normalize_coin_from_text_fn: Callable[[Optional[str]], str],
    normalize_interval_fn: Callable[[Any], str],
    build_ai_result_fn: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    is_ko = bool(re.search(r"[가-힣]", prompt))
    coin = normalize_coin_from_text_fn(ui_context.get("coin"))
    interval = normalize_interval_fn(ui_context.get("interval"), default="4h")

    if is_ko:
        questions = [
            f"{coin} {interval} 기준 RSI 역추세(Long, RSI<30)로 백테스트해줘",
            f"{coin} {interval} 기준 SMA20/SMA60 골든크로스(Long)로 백테스트해줘",
            f"{coin} {interval} 기준 볼린저 밴드 하단 반등(Long)으로 백테스트해줘",
        ]
        answer = (
            "요청이 조금 모호해서 바로 실행하면 임의 파라미터가 들어갈 수 있습니다.\n"
            "아래처럼 조건을 한 줄로 지정해 주세요. (칩을 눌러도 됩니다)\n"
            "- 코인/봉간격\n"
            "- 전략 또는 지표 조건\n"
            "- 방향(Long/Short)"
        )
    else:
        questions = [
            f"Backtest {coin} {interval} with RSI mean reversion (Long, RSI < 30)",
            f"Backtest {coin} {interval} with SMA20/SMA60 golden cross (Long)",
            f"Backtest {coin} {interval} with Bollinger lower-band rebound (Long)",
        ]
        answer = (
            "Your request is ambiguous, so using defaults would be unreliable.\n"
            "Please specify coin/interval, strategy or indicator conditions, and direction (Long/Short)."
        )

    return build_ai_result_fn(
        answer=answer,
        needs_clarification=True,
        clarifying_questions=questions,
        execution_path="clarification",
        error=None,
    )


def build_optimization_clarification_payload(
    prompt: str,
    ui_context: Dict[str, str],
    *,
    normalize_coin_from_text_fn: Callable[[Optional[str]], str],
    normalize_interval_fn: Callable[[Any], str],
    build_ai_result_fn: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    is_ko = bool(re.search(r"[가-힣]", prompt))
    coin = normalize_coin_from_text_fn(ui_context.get("coin"))
    interval = normalize_interval_fn(ui_context.get("interval"), default="4h")

    if is_ko:
        questions = [
            f"{coin} {interval} RSI 전략 백테스트 실행해줘",
            f"{coin} {interval} SMA20/SMA60 골든크로스 롱 백테스트 실행해줘",
            "방금 백테스트한 전략 파라미터 최적화해줘",
        ]
        answer = (
            "최적화 요청은 이해했지만, 지금 메시지에는 최적화할 전략 파라미터가 없습니다.\n"
            "먼저 백테스트 전략을 실행하거나 전략/조건을 명시해 주세요.\n"
            '예: "BTC 4h RSI 롱 전략 백테스트" 후 "방금 전략 최적화"'
        )
    else:
        questions = [
            f"Run a {coin} {interval} RSI long backtest",
            f"Run a {coin} {interval} SMA20/SMA60 golden-cross long backtest",
            "Optimize the latest backtested strategy parameters",
        ]
        answer = (
            "Optimization is requested, but this message does not contain executable strategy parameters.\n"
            "Run a concrete backtest strategy first, then ask for optimization."
        )

    return build_ai_result_fn(
        answer=answer,
        needs_clarification=True,
        clarifying_questions=questions,
        execution_path="optimization_clarification",
        error=None,
    )
