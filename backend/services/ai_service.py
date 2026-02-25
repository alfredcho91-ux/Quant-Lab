"""AI Service Layer
LLM을 사용하여 자연어를 백테스트 파라미터로 변환하고, 백테스트를 실행합니다.
"""
import json
import logging
import hashlib
import os
import re
import random
from typing import Dict, Any, Optional, List, TypedDict
import requests
import pandas as pd

from services.backtest_service import run_backtest_service, run_backtest_advanced_service
from services.ai_clients import (
    build_llm_client,
    ERROR_CODE_MODEL_HTTP as CLIENT_ERROR_CODE_MODEL_HTTP,
    ERROR_CODE_MODEL_NETWORK as CLIENT_ERROR_CODE_MODEL_NETWORK,
    ERROR_CODE_MODEL_RESPONSE_EMPTY as CLIENT_ERROR_CODE_MODEL_RESPONSE_EMPTY,
    ERROR_CODE_MODEL_RESPONSE_FORMAT as CLIENT_ERROR_CODE_MODEL_RESPONSE_FORMAT,
)
from services.ai_prompts import SYSTEM_PROMPT_TEMPLATE, SYSTEM_PROMPT_VERSION
from models.request import BacktestParams, AdvancedBacktestParams
from core.strategies import STRATS
from core.indicators import prepare_strategy_data, compute_trend_judgment_indicators
from config import settings
from utils.cache import DataCache
from utils.data_loader import load_data_for_analysis
from utils.stats import calculate_binomial_pvalue, wilson_confidence_interval

logger = logging.getLogger(__name__)

AI_RESPONSE_CACHE = DataCache(
    ttl_seconds=max(60, int(os.getenv("AI_RESPONSE_CACHE_TTL_SECONDS", "600")))
)

# Gemini API에서 기본으로 사용할 모델.
GEMINI_DEFAULT_MODEL = "gemini-3-flash-preview"
GEMINI_MODEL_ALIASES = {
    "gemini-3-flash": GEMINI_DEFAULT_MODEL,
    "gemini-3.0-flash": GEMINI_DEFAULT_MODEL,
    "gemini-3-flash-latest": GEMINI_DEFAULT_MODEL,
    "gemini-pro": GEMINI_DEFAULT_MODEL,
    "gemini-1.5-pro": GEMINI_DEFAULT_MODEL,
    "gemini-2.5-flash": GEMINI_DEFAULT_MODEL,
    "gemini-3.0-pro-exp": GEMINI_DEFAULT_MODEL,
    "gemini-3.0-pro-preview": GEMINI_DEFAULT_MODEL,
    "gemini-3.0-pro-preivew": GEMINI_DEFAULT_MODEL,  # 오타 버전
    "gemini-3-pro-preview": GEMINI_DEFAULT_MODEL,     # 이전 잘못된 설정
    "gemini-2.0-pro-exp-02-05": GEMINI_DEFAULT_MODEL,
}

ERROR_CODE_PROVIDER_UNSUPPORTED = "PROVIDER_UNSUPPORTED"
ERROR_CODE_API_KEY_INVALID = "API_KEY_INVALID"
ERROR_CODE_MODEL_HTTP = CLIENT_ERROR_CODE_MODEL_HTTP
ERROR_CODE_MODEL_NETWORK = CLIENT_ERROR_CODE_MODEL_NETWORK
ERROR_CODE_MODEL_RESPONSE_EMPTY = CLIENT_ERROR_CODE_MODEL_RESPONSE_EMPTY
ERROR_CODE_MODEL_RESPONSE_FORMAT = CLIENT_ERROR_CODE_MODEL_RESPONSE_FORMAT
ERROR_CODE_BACKTEST_EXECUTION = "BACKTEST_EXECUTION_ERROR"


class AIServiceResult(TypedDict, total=False):
    thought: str
    params: Optional[Dict[str, Any]]
    answer: str
    backtest_params: Optional[Dict[str, Any]]
    backtest_result: Optional[Dict[str, Any]]
    analysis_result: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarifying_questions: Optional[List[str]]
    cache_hit: Optional[bool]
    execution_path: Optional[str]
    error: Optional[str]
    error_code: Optional[str]

MISSING_VALUE_TOKENS = {
    "",
    "na",
    "n/a",
    "null",
    "none",
    "unknown",
    "undefined",
    "missing",
}
VALID_BACKTEST_INTERVALS = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
}
LOWERCASE_BACKTEST_INTERVALS = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
}
INTERVAL_ALIASES = {
    "60m": "1h",
    "120m": "2h",
    "240m": "4h",
    "d1": "1d",
    "w1": "1w",
    "1mo": "1M",
    "1month": "1M",
    "1mon": "1M",
}
MONTH_INTERVAL_PATTERNS = (
    re.compile(r"(?<![0-9A-Za-z])1M(?![0-9A-Za-z])"),
    re.compile(r"(?<![0-9A-Za-z])1\s*(?:month|months|mon|mo)(?![0-9A-Za-z])", re.IGNORECASE),
)
INTERVAL_REGEX_PATTERNS = [
    (re.compile(r"(?<![0-9A-Za-z])12h(?![0-9A-Za-z])", re.IGNORECASE), "12h"),
    (re.compile(r"(?<![0-9A-Za-z])8h(?![0-9A-Za-z])", re.IGNORECASE), "8h"),
    (re.compile(r"(?<![0-9A-Za-z])6h(?![0-9A-Za-z])", re.IGNORECASE), "6h"),
    (re.compile(r"(?<![0-9A-Za-z])4h(?![0-9A-Za-z])", re.IGNORECASE), "4h"),
    (re.compile(r"(?<![0-9A-Za-z])3d(?![0-9A-Za-z])", re.IGNORECASE), "3d"),
    (re.compile(r"(?<![0-9A-Za-z])2h(?![0-9A-Za-z])", re.IGNORECASE), "2h"),
    (re.compile(r"(?<![0-9A-Za-z])1w(?![0-9A-Za-z])", re.IGNORECASE), "1w"),
    (re.compile(r"(?<![0-9A-Za-z])1d(?![0-9A-Za-z])", re.IGNORECASE), "1d"),
    (re.compile(r"(?<![0-9A-Za-z])1h(?![0-9A-Za-z])", re.IGNORECASE), "1h"),
    (re.compile(r"(?<![0-9A-Za-z])30m(?![0-9A-Za-z])"), "30m"),
    (re.compile(r"(?<![0-9A-Za-z])15m(?![0-9A-Za-z])"), "15m"),
    (re.compile(r"(?<![0-9A-Za-z])5m(?![0-9A-Za-z])"), "5m"),
    (re.compile(r"(?<![0-9A-Za-z])3m(?![0-9A-Za-z])"), "3m"),
    (re.compile(r"(?<![0-9A-Za-z])1m(?![0-9A-Za-z])"), "1m"),
]
INTERVAL_ALIAS_REGEX_PATTERNS = [
    (re.compile(r"(?<![0-9A-Za-z])240m(?![0-9A-Za-z])", re.IGNORECASE), "4h"),
    (re.compile(r"(?<![0-9A-Za-z])120m(?![0-9A-Za-z])", re.IGNORECASE), "2h"),
    (re.compile(r"(?<![0-9A-Za-z])60m(?![0-9A-Za-z])", re.IGNORECASE), "1h"),
    (re.compile(r"(?<![0-9A-Za-z])d1(?![0-9A-Za-z])", re.IGNORECASE), "1d"),
    (re.compile(r"(?<![0-9A-Za-z])w1(?![0-9A-Za-z])", re.IGNORECASE), "1w"),
]
CONTEXT_LINE_PATTERN = re.compile(r"^\s*([a-zA-Z_]+)\s*=\s*(.+?)\s*$")
LEVERAGE_PATTERN = re.compile(
    r"(?:레버리지|leverage)\s*[:=]?\s*(\d{1,3})(?:\s*[xX배])?",
    re.IGNORECASE,
)
KOR_INTERVAL_HINTS = [
    ("15분", "15m"),
    ("30분", "30m"),
    ("1시간", "1h"),
    ("2시간", "2h"),
    ("4시간", "4h"),
    ("8시간", "8h"),
    ("12시간", "12h"),
    ("주봉", "1w"),
    ("월봉", "1M"),
    ("일봉", "1d"),
]
COMPARATOR_KEYWORD_TO_OP = {
    "이상": ">=",
    "above": ">=",
    "over": ">=",
    "greater": ">=",
    "at least": ">=",
    "이하": "<=",
    "below": "<=",
    "under": "<=",
    "less": "<=",
    "at most": "<=",
    "초과": ">",
    "미만": "<",
}
NUMERIC_INDICATOR_DEFS = [
    {
        "key": "rsi",
        "display": "RSI",
        "aliases": ["rsi"],
        "columns": ["RSI", "rsi"],
    },
    {
        "key": "adx",
        "display": "ADX",
        "aliases": ["adx"],
        "columns": ["ADX", "adx"],
    },
    {
        "key": "atr",
        "display": "ATR",
        "aliases": ["atr"],
        "columns": ["ATR", "atr"],
    },
    {
        "key": "sma20",
        "display": "SMA20",
        "aliases": ["sma20", "sma 20", "20이평"],
        "columns": ["sma20", "SMA20"],
    },
    {
        "key": "sma50",
        "display": "SMA50",
        "aliases": ["sma50", "sma 50", "50이평"],
        "columns": ["sma50", "SMA50"],
    },
    {
        "key": "sma100",
        "display": "SMA100",
        "aliases": ["sma100", "sma 100", "100이평"],
        "columns": ["sma100", "SMA100"],
    },
    {
        "key": "sma200",
        "display": "SMA200",
        "aliases": ["sma200", "sma 200", "200이평"],
        "columns": ["sma200", "SMA200", "SMA_200"],
    },
]
STOCH_GOLDEN_TOKENS = (
    "골든크로스",
    "골든 크로스",
    "골드크로스",
    "골드 크로스",
    "골크",
    "golden cross",
    "golden-cross",
    "gold cross",
    "gold-cross",
    "cross up",
)
STOCH_DEAD_TOKENS = ("데드크로스", "데크", "dead cross", "cross down")
STOCH_INTENT_TOKENS = ("stoch", "스토캐", "스토캐스틱", "슬로우", "slow", "3스토", "533스토")
OPTIMIZATION_HINT_TOKENS = (
    "최적화",
    "튜닝",
    "파라미터 조정",
    "parameter tune",
    "parameter tuning",
    "optimize",
    "optimization",
    "tune this",
    "best parameter",
    "best params",
)
OPTIMIZATION_TRIALS = max(8, int(os.getenv("AI_OPTIMIZATION_TRIALS", "18")))
OPTIMIZATION_TRAIN_RATIO = min(
    0.95,
    max(0.3, float(os.getenv("AI_OPTIMIZATION_TRAIN_RATIO", "0.7"))),
)
OPTIMIZATION_MONTE_CARLO_RUNS = max(
    100,
    int(os.getenv("AI_OPTIMIZATION_MONTE_CARLO_RUNS", "300")),
)
OPTIMIZATION_FEATURE_LABELS = [
    ("tp_pct", "TP%"),
    ("sl_pct", "SL%"),
    ("max_bars", "MaxBars"),
    ("rsi_ob", "RSI_OB"),
    ("sma1_len", "SMA1"),
    ("sma2_len", "SMA2"),
    ("adx_thr", "ADX"),
    ("bb_length", "BB Length"),
    ("bb_std_mult", "BB Std"),
    ("atr_length", "ATR Length"),
    ("kc_mult", "KC Mult"),
    ("vol_spike_k", "Vol Spike K"),
    ("macd_fast", "MACD Fast"),
    ("macd_slow", "MACD Slow"),
    ("macd_signal", "MACD Signal"),
    ("leverage", "Leverage"),
]


def _parse_operator_from_keyword(keyword: str, fallback_value: float) -> str:
    normalized = keyword.strip().lower()
    for token, op in COMPARATOR_KEYWORD_TO_OP.items():
        if token in normalized:
            return op
    return ">=" if fallback_value >= 0 else "<="


def _resolve_indicator_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


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

        # 영어형 fallback: "rsi above 35"
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


def _detect_stoch_pair(prompt: str) -> tuple[str, str, str]:
    lower = prompt.lower()
    if (
        "20-12-12" in lower
        or "1스토" in prompt
        or "1번 스토" in prompt
        or "section 1" in lower
    ):
        return "stoch_rsi_20k", "stoch_rsi_20d", "20-12-12"
    if (
        "10-6-6" in lower
        or "2스토" in prompt
        or "2번 스토" in prompt
        or "section 2" in lower
    ):
        return "stoch_rsi_10k", "stoch_rsi_10d", "10-6-6"
    if (
        "5-3-3" in lower
        or "3스토" in prompt
        or "533스토" in prompt
        or "section 3" in lower
    ):
        return "stoch_rsi_5k", "stoch_rsi_5d", "5-3-3"
    # 기본은 3스토(5-3-3)로 간주
    return "stoch_rsi_5k", "stoch_rsi_5d", "5-3-3"


def _contains_stochastic_intent(prompt: str) -> bool:
    lower = (prompt or "").lower()
    if any(token in lower for token in STOCH_INTENT_TOKENS):
        return True
    return bool(re.search(r"(?:^|[^0-9a-zA-Z])(?:\d+\s*스토|533\s*스토)(?:$|[^0-9a-zA-Z])", prompt or "", re.IGNORECASE))


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


def _split_prompt_and_ui_context(prompt: str) -> tuple[str, Dict[str, str]]:
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


def _build_ai_result(
    *,
    answer: str,
    backtest_params: Optional[Dict[str, Any]] = None,
    backtest_result: Optional[Dict[str, Any]] = None,
    analysis_result: Optional[Dict[str, Any]] = None,
    needs_clarification: bool = False,
    clarifying_questions: Optional[List[str]] = None,
    cache_hit: Optional[bool] = False,
    execution_path: Optional[str] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
) -> AIServiceResult:
    return {
        "answer": answer,
        "backtest_params": backtest_params,
        "backtest_result": backtest_result,
        "analysis_result": analysis_result,
        "needs_clarification": bool(needs_clarification),
        "clarifying_questions": clarifying_questions or None,
        "cache_hit": cache_hit,
        "execution_path": execution_path,
        "error": error,
        "error_code": error_code,
    }


def _normalize_result_payload(result: Dict[str, Any], *, execution_path: str, cache_hit: bool) -> AIServiceResult:
    return _build_ai_result(
        answer=str(result.get("answer", "")),
        backtest_params=result.get("backtest_params"),
        backtest_result=result.get("backtest_result"),
        analysis_result=result.get("analysis_result"),
        needs_clarification=bool(result.get("needs_clarification", False)),
        clarifying_questions=result.get("clarifying_questions"),
        cache_hit=cache_hit,
        execution_path=execution_path,
        error=result.get("error"),
        error_code=result.get("error_code"),
    )


def _compact_history_for_cache(history: Optional[list]) -> List[Dict[str, str]]:
    compact: List[Dict[str, str]] = []
    if not isinstance(history, list):
        return compact
    for item in history[-6:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user")).strip().lower()
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        compact.append({"role": role, "content": content[:240]})
    return compact


def _build_ai_cache_key(
    *,
    clean_prompt: str,
    ui_context: Dict[str, str],
    provider: str,
    model: str,
    temperature: float,
    history: Optional[list],
) -> str:
    payload = {
        "v": 4,
        "prompt_version": SYSTEM_PROMPT_VERSION,
        "prompt": clean_prompt.strip(),
        "ui_context": dict(sorted(ui_context.items())),
        "provider": provider,
        "model": model,
        "temperature": round(float(temperature), 3),
        "history_tail": _compact_history_for_cache(history),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"ai_research:{digest}"


def _infer_interval_from_prompt(prompt: str, fallback: str) -> str:
    if not prompt:
        return fallback

    # Month first: avoid confusing "1M"(month) with "1m"(minute).
    if any(pattern.search(prompt) for pattern in MONTH_INTERVAL_PATTERNS):
        return "1M"

    # explicit shorthand with strict token boundary
    for pattern, interval in INTERVAL_REGEX_PATTERNS:
        if pattern.search(prompt):
            return interval

    # alias fallback
    for pattern, canonical in INTERVAL_ALIAS_REGEX_PATTERNS:
        if pattern.search(prompt):
            return canonical

    # Korean hints
    for keyword, interval in KOR_INTERVAL_HINTS:
        if keyword in prompt:
            return interval
    # "N일 연속"은 일봉 의도로 간주
    if re.search(r"\d+\s*일\s*연속", prompt):
        return "1d"
    return fallback


def _normalize_coin_from_text(value: Optional[str], fallback: str = "BTC") -> str:
    if not value:
        return fallback
    symbol = value.strip().upper().replace("/USDT", "").replace("USDT", "")
    symbol = "".join(ch for ch in symbol if ch.isalnum())
    if 2 <= len(symbol) <= 20:
        return symbol
    return fallback


def _contains_probability_intent(prompt: str) -> bool:
    lowered = prompt.lower()
    probability_tokens = ("확률", "probability", "가능성")
    candle_tokens = ("양봉", "음봉", "bull", "bear", "green", "red", "다음봉", "다음날", "next")
    return any(token in lowered for token in probability_tokens) and any(
        token in lowered for token in candle_tokens
    )


def _looks_like_optimization_request(prompt: str) -> bool:
    lowered = (prompt or "").lower()
    return any(token in lowered for token in OPTIMIZATION_HINT_TOKENS)


def _build_float_candidates(
    value: float,
    *,
    minimum: float,
    maximum: float,
    precision: int,
) -> List[float]:
    multipliers = (0.7, 0.85, 1.0, 1.15, 1.35)
    values = {
        round(min(max(value * mult, minimum), maximum), precision)
        for mult in multipliers
    }
    values.add(round(min(max(value, minimum), maximum), precision))
    return sorted(values)


def _build_int_candidates(
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> List[int]:
    multipliers = (0.7, 0.85, 1.0, 1.15, 1.35)
    values = {
        max(minimum, min(maximum, int(round(value * mult))))
        for mult in multipliers
    }
    values.add(max(minimum, min(maximum, int(value))))
    return sorted(values)


def _build_optimization_space(base: BacktestParams) -> Dict[str, List[Any]]:
    return {
        "tp_pct": _build_float_candidates(base.tp_pct, minimum=0.1, maximum=8.0, precision=2),
        "sl_pct": _build_float_candidates(base.sl_pct, minimum=0.1, maximum=6.0, precision=2),
        "max_bars": _build_int_candidates(base.max_bars, minimum=4, maximum=800),
        "rsi_ob": _build_int_candidates(base.rsi_ob, minimum=50, maximum=90),
        "sma1_len": _build_int_candidates(base.sma1_len, minimum=3, maximum=400),
        "sma2_len": _build_int_candidates(base.sma2_len, minimum=5, maximum=1200),
        "adx_thr": _build_int_candidates(base.adx_thr, minimum=5, maximum=60),
        "bb_length": _build_int_candidates(base.bb_length, minimum=5, maximum=120),
        "bb_std_mult": _build_float_candidates(base.bb_std_mult, minimum=0.5, maximum=4.0, precision=2),
        "atr_length": _build_int_candidates(base.atr_length, minimum=5, maximum=120),
        "kc_mult": _build_float_candidates(base.kc_mult, minimum=0.5, maximum=4.0, precision=2),
        "vol_spike_k": _build_float_candidates(base.vol_spike_k, minimum=0.5, maximum=10.0, precision=2),
        "macd_fast": _build_int_candidates(base.macd_fast, minimum=4, maximum=40),
        "macd_slow": _build_int_candidates(base.macd_slow, minimum=8, maximum=80),
        "macd_signal": _build_int_candidates(base.macd_signal, minimum=3, maximum=30),
    }


def _optimization_signature(params: BacktestParams) -> tuple:
    return (
        params.tp_pct,
        params.sl_pct,
        params.max_bars,
        params.rsi_ob,
        params.sma1_len,
        params.sma2_len,
        params.adx_thr,
        params.bb_length,
        params.bb_std_mult,
        params.atr_length,
        params.kc_mult,
        params.vol_spike_k,
        params.macd_fast,
        params.macd_slow,
        params.macd_signal,
    )


def _score_backtest_summary(summary: Dict[str, Any]) -> float:
    trades = int(summary.get("n_trades") or 0)
    win_rate = float(summary.get("win_rate") or 0.0)
    total_pnl = float(summary.get("total_pnl") or 0.0)
    avg_pnl = float(summary.get("avg_pnl") or 0.0)
    liq_count = int(summary.get("liq_count") or 0)

    score = (total_pnl * 0.75) + (avg_pnl * 0.45) + ((win_rate - 50.0) * 0.3) - (liq_count * 3.5)
    if trades < 10:
        score -= (10 - trades) * 0.8

    trade_weight = max(0.35, min(1.0, trades / 80.0))
    return score * trade_weight


def _extract_advanced_summary(result: Dict[str, Any], section: str) -> Dict[str, Any]:
    section_payload = result.get(section)
    if isinstance(section_payload, dict):
        summary = section_payload.get("summary")
        if isinstance(summary, dict):
            return summary
    return {}


def _to_advanced_params(candidate: BacktestParams) -> AdvancedBacktestParams:
    payload = candidate.model_dump()
    payload["train_ratio"] = OPTIMIZATION_TRAIN_RATIO
    payload["monte_carlo_runs"] = OPTIMIZATION_MONTE_CARLO_RUNS
    return AdvancedBacktestParams(**payload)


def _score_advanced_backtest(advanced_result: Dict[str, Any]) -> float:
    in_summary = _extract_advanced_summary(advanced_result, "in_sample")
    out_summary = _extract_advanced_summary(advanced_result, "out_of_sample")
    full_summary = _extract_advanced_summary(advanced_result, "full")

    if not out_summary and not full_summary:
        return float("-inf")

    focus_summary = out_summary if out_summary else full_summary
    in_score = _score_backtest_summary(in_summary if in_summary else focus_summary)
    focus_score = _score_backtest_summary(focus_summary)
    full_score = _score_backtest_summary(full_summary if full_summary else focus_summary)

    in_win = float(in_summary.get("win_rate") or 0.0)
    focus_win = float(focus_summary.get("win_rate") or 0.0)
    in_pnl = float(in_summary.get("total_pnl") or 0.0)
    focus_pnl = float(focus_summary.get("total_pnl") or 0.0)
    in_trades = int(in_summary.get("n_trades") or 0)
    focus_trades = int(focus_summary.get("n_trades") or 0)

    # train 대비 OOS 괴리가 크면 감점하여 과최적화를 억제한다.
    stability_penalty = (
        abs(in_win - focus_win) * 0.25
        + max(0.0, in_pnl - focus_pnl) * 0.15
        + max(0, in_trades - focus_trades) * 0.03
    )
    if focus_trades < 5:
        stability_penalty += (5 - focus_trades) * 1.2

    focus_weight = 0.75 if out_summary else 0.45
    return (focus_score * focus_weight) + (full_score * (1.0 - focus_weight)) + (in_score * 0.05) - stability_penalty


def _normalize_summary_for_ui(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "n_trades": int(summary.get("n_trades") or 0),
        "win_rate": float(summary.get("win_rate") or 0.0),
        "total_pnl": float(summary.get("total_pnl") or 0.0),
        "avg_pnl": float(summary.get("avg_pnl") or 0.0),
        "liq_count": int(summary.get("liq_count") or 0),
        "regime_stats": summary.get("regime_stats") if isinstance(summary.get("regime_stats"), list) else [],
    }


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _format_param_value(key: str, value: float) -> float:
    if key in {"tp_pct", "sl_pct", "bb_std_mult", "kc_mult", "vol_spike_k"}:
        return round(value, 2)
    return round(value, 1)


def _build_optimization_characteristics(
    trial_rows: List[Dict[str, Any]],
    prompt: str,
) -> Optional[Dict[str, Any]]:
    if len(trial_rows) < 8:
        return None

    is_ko = bool(re.search(r"[가-힣]", prompt or ""))
    ordered = sorted(trial_rows, key=lambda row: float(row.get("score") or float("-inf")))
    bucket_size = max(2, len(ordered) // 4)
    bottom_rows = ordered[:bucket_size]
    top_rows = ordered[-bucket_size:]

    highlights: List[Dict[str, Any]] = []
    for key, label in OPTIMIZATION_FEATURE_LABELS:
        all_values = [float(row["params"][key]) for row in trial_rows if key in row.get("params", {})]
        if len(all_values) < bucket_size * 2:
            continue

        min_value = min(all_values)
        max_value = max(all_values)
        span = max_value - min_value
        if span <= 1e-9:
            continue

        top_values = [float(row["params"][key]) for row in top_rows if key in row.get("params", {})]
        bottom_values = [float(row["params"][key]) for row in bottom_rows if key in row.get("params", {})]
        if not top_values or not bottom_values:
            continue

        top_mean = _mean(top_values)
        bottom_mean = _mean(bottom_values)
        effect_ratio = abs(top_mean - bottom_mean) / span
        if effect_ratio < 0.18:
            continue

        higher_is_better = top_mean > bottom_mean
        if is_ko:
            interpretation = "높을수록 성과 우세" if higher_is_better else "낮을수록 성과 우세"
        else:
            interpretation = "Higher tends to outperform" if higher_is_better else "Lower tends to outperform"

        highlights.append(
            {
                "param": key,
                "label": label,
                "direction": "higher_better" if higher_is_better else "lower_better",
                "top_mean": _format_param_value(key, top_mean),
                "bottom_mean": _format_param_value(key, bottom_mean),
                "effect_pct": round(effect_ratio * 100.0, 1),
                "interpretation": interpretation,
            }
        )

    if not highlights:
        return None

    highlights.sort(key=lambda item: float(item["effect_pct"]), reverse=True)
    highlights = highlights[:5]

    top_oos_pnl = _mean([float(row.get("oos_total_pnl") or 0.0) for row in top_rows])
    bottom_oos_pnl = _mean([float(row.get("oos_total_pnl") or 0.0) for row in bottom_rows])
    top_oos_win_rate = _mean([float(row.get("oos_win_rate") or 0.0) for row in top_rows])
    bottom_oos_win_rate = _mean([float(row.get("oos_win_rate") or 0.0) for row in bottom_rows])

    return {
        "analysis_type": "optimization_characteristics",
        "summary": {
            "trial_count": len(trial_rows),
            "bucket_size": bucket_size,
            "top_avg_oos_pnl": round(top_oos_pnl, 2),
            "bottom_avg_oos_pnl": round(bottom_oos_pnl, 2),
            "top_avg_oos_win_rate": round(top_oos_win_rate, 2),
            "bottom_avg_oos_win_rate": round(bottom_oos_win_rate, 2),
        },
        "highlights": highlights,
    }


def _build_ui_result_from_advanced_payload(advanced_result: Dict[str, Any]) -> Dict[str, Any]:
    chart_data = advanced_result.get("chart_data") if isinstance(advanced_result.get("chart_data"), list) else []
    trades = advanced_result.get("trades") if isinstance(advanced_result.get("trades"), list) else []
    full_summary = _extract_advanced_summary(advanced_result, "full")
    return {
        "success": True,
        "chart_data": chart_data,
        "trades": trades,
        "summary": _normalize_summary_for_ui(full_summary),
    }


def _format_optimization_summary(
    *,
    prompt: str,
    base_summary: Dict[str, Any],
    best_summary: Dict[str, Any],
    evaluated_count: int,
    best_params: BacktestParams,
) -> str:
    is_ko = bool(re.search(r"[가-힣]", prompt or ""))
    base_pnl = float(base_summary.get("total_pnl") or 0.0)
    best_pnl = float(best_summary.get("total_pnl") or 0.0)
    base_wr = float(base_summary.get("win_rate") or 0.0)
    best_wr = float(best_summary.get("win_rate") or 0.0)
    pnl_delta = best_pnl - base_pnl
    wr_delta = best_wr - base_wr

    if is_ko:
        return (
            f"[자동 최적화 완료] OOS 검증기준 탐색 {evaluated_count}회\n"
            f"- 기준(OOS): 수익률 {base_pnl:.2f}%, 승률 {base_wr:.2f}%\n"
            f"- 최적(OOS): 수익률 {best_pnl:.2f}%, 승률 {best_wr:.2f}%\n"
            f"- 개선(OOS): 수익률 {pnl_delta:+.2f}%p, 승률 {wr_delta:+.2f}%p\n"
            f"- 추천 파라미터: TP {best_params.tp_pct:.2f}% / SL {best_params.sl_pct:.2f}% / "
            f"MaxBars {best_params.max_bars} / RSI_OB {best_params.rsi_ob}"
        )

    return (
        f"[Auto Optimization Complete] OOS-focused {evaluated_count} trials\n"
        f"- Baseline (OOS): PnL {base_pnl:.2f}%, WinRate {base_wr:.2f}%\n"
        f"- Best (OOS): PnL {best_pnl:.2f}%, WinRate {best_wr:.2f}%\n"
        f"- Delta (OOS): PnL {pnl_delta:+.2f}pp, WinRate {wr_delta:+.2f}pp\n"
        f"- Suggested params: TP {best_params.tp_pct:.2f}% / SL {best_params.sl_pct:.2f}% / "
        f"MaxBars {best_params.max_bars} / RSI_OB {best_params.rsi_ob}"
    )


def _run_backtest_parameter_optimization(base_params: BacktestParams, prompt: str) -> Dict[str, Any]:
    seed_material = (
        f"{prompt}|{base_params.coin}|{base_params.interval}|"
        f"{base_params.strategy_id}|{base_params.direction}"
    )
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    space = _build_optimization_space(base_params)
    base_payload = base_params.model_dump()

    candidates: List[BacktestParams] = [base_params]
    signatures = {_optimization_signature(base_params)}
    attempts = 0
    max_attempts = max(40, OPTIMIZATION_TRIALS * 30)

    while len(candidates) < OPTIMIZATION_TRIALS and attempts < max_attempts:
        attempts += 1
        payload = dict(base_payload)
        payload["tp_pct"] = rng.choice(space["tp_pct"])
        payload["sl_pct"] = rng.choice(space["sl_pct"])
        payload["max_bars"] = rng.choice(space["max_bars"])
        payload["rsi_ob"] = rng.choice(space["rsi_ob"])
        payload["adx_thr"] = rng.choice(space["adx_thr"])
        payload["bb_length"] = rng.choice(space["bb_length"])
        payload["bb_std_mult"] = rng.choice(space["bb_std_mult"])
        payload["atr_length"] = rng.choice(space["atr_length"])
        payload["kc_mult"] = rng.choice(space["kc_mult"])
        payload["vol_spike_k"] = rng.choice(space["vol_spike_k"])

        sma1 = rng.choice(space["sma1_len"])
        sma2_choices = [value for value in space["sma2_len"] if value >= sma1]
        if not sma2_choices:
            continue
        payload["sma1_len"] = sma1
        payload["sma2_len"] = rng.choice(sma2_choices)

        macd_fast = rng.choice(space["macd_fast"])
        macd_slow_choices = [value for value in space["macd_slow"] if value > macd_fast]
        if not macd_slow_choices:
            continue
        macd_slow = rng.choice(macd_slow_choices)
        macd_signal_choices = [value for value in space["macd_signal"] if value < macd_slow]
        if not macd_signal_choices:
            continue
        payload["macd_fast"] = macd_fast
        payload["macd_slow"] = macd_slow
        payload["macd_signal"] = rng.choice(macd_signal_choices)

        try:
            candidate = BacktestParams(**payload)
        except Exception:
            continue

        signature = _optimization_signature(candidate)
        if signature in signatures:
            continue
        signatures.add(signature)
        candidates.append(candidate)

    best_params: Optional[BacktestParams] = None
    best_advanced_result: Optional[Dict[str, Any]] = None
    best_summary: Dict[str, Any] = {}
    best_score = float("-inf")
    base_summary: Dict[str, Any] = {}
    evaluated = 0
    trial_rows: List[Dict[str, Any]] = []

    # Baseline must come from base params, not from first successful random trial.
    try:
        base_advanced = run_backtest_advanced_service(_to_advanced_params(base_params))
        if isinstance(base_advanced, dict) and base_advanced.get("success"):
            base_focus_summary = _extract_advanced_summary(base_advanced, "out_of_sample")
            if not base_focus_summary:
                base_focus_summary = _extract_advanced_summary(base_advanced, "full")
            if base_focus_summary:
                base_summary = base_focus_summary
    except Exception:
        logger.exception("Failed to compute base optimization summary. Fallback baseline will be used.")

    for idx, candidate in enumerate(candidates):
        try:
            advanced_params = _to_advanced_params(candidate)
            advanced_result = run_backtest_advanced_service(advanced_params)
        except Exception:
            logger.exception("Auto optimization trial failed unexpectedly (trial=%s)", idx + 1)
            continue

        if not isinstance(advanced_result, dict) or not advanced_result.get("success"):
            continue

        focus_summary = _extract_advanced_summary(advanced_result, "out_of_sample")
        if not focus_summary:
            focus_summary = _extract_advanced_summary(advanced_result, "full")
        if not focus_summary:
            continue

        score = _score_advanced_backtest(advanced_result)
        if score == float("-inf"):
            continue
        evaluated += 1

        trial_rows.append(
            {
                "score": score,
                "params": candidate.model_dump(),
                "oos_total_pnl": float(focus_summary.get("total_pnl") or 0.0),
                "oos_win_rate": float(focus_summary.get("win_rate") or 0.0),
                "oos_trades": int(focus_summary.get("n_trades") or 0),
            }
        )

        if score > best_score:
            best_score = score
            best_params = candidate
            best_advanced_result = advanced_result
            best_summary = focus_summary

    if best_params is None or best_advanced_result is None:
        return {
            "answer": "Auto optimization failed: no valid backtest trials were produced.",
            "params": None,
            "backtest_result": None,
            "error": "No valid optimization trial result.",
        }

    if not base_summary:
        base_summary = best_summary

    summary_text = _format_optimization_summary(
        prompt=prompt,
        base_summary=base_summary,
        best_summary=best_summary,
        evaluated_count=evaluated,
        best_params=best_params,
    )
    characteristics = _build_optimization_characteristics(trial_rows, prompt)

    try:
        best_result = run_backtest_service(best_params)
        if not isinstance(best_result, dict) or not best_result.get("success"):
            best_result = _build_ui_result_from_advanced_payload(best_advanced_result)
    except Exception:
        logger.exception("Failed to build final best-result payload. Falling back to advanced payload view.")
        best_result = _build_ui_result_from_advanced_payload(best_advanced_result)

    return {
        "answer": summary_text,
        "params": best_params.model_dump(),
        "backtest_result": best_result,
        "analysis_result": characteristics,
        "error": None,
    }


def _looks_ambiguous_prompt(prompt: str) -> bool:
    text = (prompt or "").strip()
    lowered = text.lower()
    if not text:
        return True
    if _contains_probability_intent(text):
        return False

    strategy_tokens = [str(item.get("id", "")).lower() for item in STRATS if item.get("id")]
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


def _build_clarification_payload(
    prompt: str,
    ui_context: Dict[str, str],
) -> Dict[str, Any]:
    is_ko = bool(re.search(r"[가-힣]", prompt))
    coin = _normalize_coin_from_text(ui_context.get("coin"), fallback="BTC")
    interval = _normalize_interval(ui_context.get("interval"), default="4h")

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

    return _build_ai_result(
        answer=answer,
        needs_clarification=True,
        clarifying_questions=questions,
        execution_path="clarification",
        error=None,
    )


def _build_optimization_clarification_payload(
    prompt: str,
    ui_context: Dict[str, str],
) -> Dict[str, Any]:
    is_ko = bool(re.search(r"[가-힣]", prompt))
    coin = _normalize_coin_from_text(ui_context.get("coin"), fallback="BTC")
    interval = _normalize_interval(ui_context.get("interval"), default="4h")

    if is_ko:
        questions = [
            f"{coin} {interval} RSI 전략 백테스트 실행해줘",
            f"{coin} {interval} SMA20/SMA60 골든크로스 롱 백테스트 실행해줘",
            "방금 백테스트한 전략 파라미터 최적화해줘",
        ]
        answer = (
            "최적화 요청은 이해했지만, 지금 메시지에는 최적화할 전략 파라미터가 없습니다.\n"
            "먼저 백테스트 전략을 실행하거나 전략/조건을 명시해 주세요.\n"
            "예: \"BTC 4h RSI 롱 전략 백테스트\" 후 \"방금 전략 최적화\""
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

    return _build_ai_result(
        answer=answer,
        needs_clarification=True,
        clarifying_questions=questions,
        execution_path="optimization_clarification",
        error=None,
    )


def _map_candle_side(token: str) -> Optional[str]:
    t = token.strip().lower()
    if t in {"양봉", "bull", "bullish", "green", "상승"}:
        return "bull"
    if t in {"음봉", "bear", "bearish", "red", "하락"}:
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

    # 연속 조건이 명시된 경우(숫자 생략)만 기본 2봉으로 보정
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

    op = (match.group(1) or "").strip()
    value = float(match.group(2))

    if not op:
        lowered = prompt.lower()
        if any(token in lowered for token in ("이하", "below", "less", "under")):
            op = "<="
        elif any(token in lowered for token in ("이상", "above", "greater", "over")):
            op = ">="
        else:
            op = ">=" if value >= 0 else "<="
    if op == "==":
        op = "="
    return {
        "operator": op,
        "threshold": value,
        "span": match.span(),
    }


def _apply_comparator(series: pd.Series, operator: str, threshold: float) -> pd.Series:
    if operator == ">":
        return series > threshold
    if operator == ">=":
        return series >= threshold
    if operator == "<":
        return series < threshold
    if operator == "<=":
        return series <= threshold
    return series == threshold


def _coerce_mask(mask: pd.Series) -> pd.Series:
    return mask.fillna(False).astype(bool)


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


def _sorted_condition_specs(condition_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _key(spec: Dict[str, Any]) -> tuple[int, int]:
        span = spec.get("span")
        if isinstance(span, tuple) and len(span) == 2:
            return int(span[0]), int(span[1])
        order = int(spec.get("order", 0))
        return 10**9 + order, 10**9 + order

    return sorted(condition_specs, key=_key)


def _build_expression_tokens(prompt: str, condition_specs: List[Dict[str, Any]]) -> tuple[List[str], Dict[str, Dict[str, Any]]]:
    if not condition_specs:
        return [], {}

    ordered_specs = _sorted_condition_specs(condition_specs)
    token_map: Dict[str, Dict[str, Any]] = {}
    for idx, spec in enumerate(ordered_specs, start=1):
        token = f"C{idx}"
        spec["token"] = token
        token_map[token] = spec

    replaced = prompt
    span_specs = [spec for spec in ordered_specs if isinstance(spec.get("span"), tuple)]
    span_specs.sort(key=lambda item: item["span"][0], reverse=True)
    for spec in span_specs:
        start, end = spec["span"]
        if start < 0 or end <= start or end > len(replaced):
            continue
        replaced = replaced[:start] + f" {spec['token']} " + replaced[end:]

    normalized = _normalize_expression_text(replaced).upper()
    tokens = re.findall(r"C\d+|AND|OR|NOT|\(|\)", normalized)

    existing_tokens = set(tokens)
    for spec in ordered_specs:
        token = spec["token"]
        if token not in existing_tokens:
            if tokens:
                tokens.extend(["AND", token])
            else:
                tokens.append(token)
            existing_tokens.add(token)

    return tokens, token_map


def _insert_implicit_and(tokens: List[str]) -> List[str]:
    if not tokens:
        return []

    def _is_operand(tok: str) -> bool:
        return tok.startswith("C")

    output: List[str] = []
    prev: Optional[str] = None
    for tok in tokens:
        if prev is not None:
            if (_is_operand(prev) or prev == ")") and (_is_operand(tok) or tok in {"(", "NOT"}):
                output.append("AND")
        output.append(tok)
        prev = tok
    return output


def _infix_to_postfix(tokens: List[str]) -> List[str]:
    precedence = {"OR": 1, "AND": 2, "NOT": 3}
    right_assoc = {"NOT"}
    output: List[str] = []
    stack: List[str] = []

    for tok in tokens:
        if tok.startswith("C"):
            output.append(tok)
            continue
        if tok in {"AND", "OR", "NOT"}:
            while stack and stack[-1] in precedence:
                top = stack[-1]
                if (tok in right_assoc and precedence[tok] < precedence[top]) or (
                    tok not in right_assoc and precedence[tok] <= precedence[top]
                ):
                    output.append(stack.pop())
                else:
                    break
            stack.append(tok)
            continue
        if tok == "(":
            stack.append(tok)
            continue
        if tok == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()
            continue

    while stack:
        top = stack.pop()
        if top in {"(", ")"}:
            raise ValueError("Mismatched parentheses")
        output.append(top)
    return output


def _eval_postfix_mask(postfix: List[str], token_map: Dict[str, Dict[str, Any]], index: pd.Index) -> pd.Series:
    stack: List[pd.Series] = []
    for tok in postfix:
        if tok.startswith("C"):
            spec = token_map.get(tok)
            if spec is None:
                raise ValueError(f"Unknown token: {tok}")
            stack.append(_coerce_mask(spec["mask"]))
            continue

        if tok == "NOT":
            if not stack:
                raise ValueError("Invalid NOT expression")
            val = stack.pop()
            stack.append(_coerce_mask(~val))
            continue

        if tok in {"AND", "OR"}:
            if len(stack) < 2:
                raise ValueError(f"Invalid binary expression for {tok}")
            right = _coerce_mask(stack.pop())
            left = _coerce_mask(stack.pop())
            merged = left & right if tok == "AND" else left | right
            stack.append(_coerce_mask(merged))
            continue

    if len(stack) != 1:
        raise ValueError("Invalid expression stack state")
    final_mask = _coerce_mask(stack[0])
    if not final_mask.index.equals(index):
        final_mask = final_mask.reindex(index, fill_value=False)
    return final_mask


def _format_expression_tokens(tokens: List[str], token_map: Dict[str, Dict[str, Any]]) -> str:
    parts: List[str] = []
    for tok in tokens:
        if tok in {"AND", "OR", "NOT", "(", ")"}:
            parts.append(tok)
            continue
        spec = token_map.get(tok)
        parts.append(spec["label"] if spec else tok)
    return " ".join(parts).strip()


def _evaluate_condition_expression(
    prompt: str,
    condition_specs: List[Dict[str, Any]],
    index: pd.Index,
) -> tuple[pd.Series, List[str], str]:
    if not condition_specs:
        return pd.Series(True, index=index), [], "조건 없음(전체 구간)"

    raw_tokens, token_map = _build_expression_tokens(prompt, condition_specs)
    infix_tokens = _insert_implicit_and(raw_tokens)
    try:
        postfix = _infix_to_postfix(infix_tokens)
        mask = _eval_postfix_mask(postfix, token_map, index)
    except Exception:
        # 실패 시 안전하게 기존 동작(AND 체인)으로 폴백
        mask = pd.Series(True, index=index)
        infix_tokens = []
        for spec in _sorted_condition_specs(condition_specs):
            mask &= _coerce_mask(spec["mask"])
            if infix_tokens:
                infix_tokens.append("AND")
            token = spec.get("token")
            if not token:
                token = f"C{len(infix_tokens) + 1}"
            infix_tokens.append(token)
            token_map[token] = spec
        mask = _coerce_mask(mask)

    condition_text = _format_expression_tokens(infix_tokens, token_map)
    return mask, infix_tokens, condition_text


def _reliability_label(sample_count: int) -> str:
    if sample_count < 10:
        return "Low Reliability"
    if sample_count < 30:
        return "Medium Reliability"
    return "High Reliability"


def _safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _calculate_gati_index(
    probability_rate: Optional[float],
    p_value: Optional[float],
    sample_count: int,
    reliability: str,
) -> float:
    probability = _safe_float(probability_rate)
    if probability is None or sample_count <= 0:
        return 0.0

    edge_score = min(100.0, abs(probability - 50.0) * 2.0)
    p_val = _safe_float(p_value)
    significance_score = 0.0 if p_val is None else max(0.0, min(100.0, (1.0 - min(1.0, max(0.0, p_val))) * 100.0))
    sample_score = max(0.0, min(100.0, sample_count / 120.0 * 100.0))
    reliability_score = {
        "Low Reliability": 35.0,
        "Medium Reliability": 65.0,
        "High Reliability": 90.0,
    }.get(reliability, 50.0)

    gati = (
        edge_score * 0.45
        + significance_score * 0.25
        + sample_score * 0.20
        + reliability_score * 0.10
    )
    return round(max(0.0, min(100.0, gati)), 2)


def _p_value_reliability_label(p_value: Optional[float]) -> str:
    val = _safe_float(p_value)
    if val is None:
        return "N/A"
    if val < 0.01:
        return "Very High"
    if val < 0.05:
        return "High"
    if val < 0.1:
        return "Medium"
    return "Low"


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


def _run_conditional_probability_analysis(prompt: str, ui_context: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not _contains_probability_intent(prompt):
        return None

    coin = _normalize_coin_from_text(ui_context.get("coin"), fallback="BTC")
    interval = _normalize_interval(
        _infer_interval_from_prompt(prompt, ui_context.get("interval", "4h")),
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

    df, source = load_data_for_analysis(coin, interval, use_csv=True, total_candles=3000)
    prepared = prepare_strategy_data(df.copy())
    prepared = compute_trend_judgment_indicators(prepared.copy())
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
    ci = wilson_confidence_interval(success_count, sample_count) if sample_count > 0 else {}
    ci_lower = _safe_float(ci.get("ci_lower"))
    ci_upper = _safe_float(ci.get("ci_upper"))
    p_value = (
        _safe_float(calculate_binomial_pvalue(success_count, sample_count, null_prob=0.5))
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


def _extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
    if not clean_text:
        return None

    try:
        parsed = json.loads(clean_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(clean_text):
        if ch != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(clean_text[idx:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        token = value.strip().lower()
        return token in MISSING_VALUE_TOKENS
    return False


def _normalize_leverage(value: Any, default: int = 1) -> int:
    if _is_missing_value(value):
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


def _extract_leverage_from_prompt(prompt: str) -> Optional[int]:
    match = LEVERAGE_PATTERN.search(prompt or "")
    if not match:
        return None
    try:
        value = int(match.group(1))
    except ValueError:
        return None
    return max(1, min(125, value))


def _normalize_coin(value: Any, default: str = "BTC") -> str:
    if _is_missing_value(value):
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


def _normalize_interval(value: Any, default: str = "4h") -> str:
    if _is_missing_value(value):
        return default
    if not isinstance(value, str):
        return default

    interval = value.strip()
    lowered = interval.lower()

    if interval in VALID_BACKTEST_INTERVALS:
        return interval
    if lowered in INTERVAL_ALIASES:
        return INTERVAL_ALIASES[lowered]
    if lowered in LOWERCASE_BACKTEST_INTERVALS:
        return lowered
    return default


def _normalize_direction(value: Any, default: str = "Long") -> str:
    if _is_missing_value(value):
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


def _normalize_strategy_id(value: Any, default: str = "RSI") -> str:
    valid_ids = [str(item["id"]) for item in STRATS]
    valid_id_set = set(valid_ids)
    normalized_index = {sid.lower(): sid for sid in valid_ids}
    alias = {
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

    fallback = default if default in valid_id_set else valid_ids[0]
    if _is_missing_value(value):
        return fallback
    if not isinstance(value, str):
        return fallback

    token = value.strip()
    if token in valid_id_set:
        return token

    lowered = token.lower()
    if lowered in alias and alias[lowered] in valid_id_set:
        return alias[lowered]
    if lowered in normalized_index:
        return normalized_index[lowered]
    return fallback


def _sanitize_backtest_params(raw_params: Any) -> Dict[str, Any]:
    params = dict(raw_params) if isinstance(raw_params, dict) else {}
    sanitized = dict(params)
    sanitized["coin"] = _normalize_coin(params.get("coin"))
    sanitized["interval"] = _normalize_interval(params.get("interval"))
    sanitized["strategy_id"] = _normalize_strategy_id(params.get("strategy_id"))
    sanitized["direction"] = _normalize_direction(params.get("direction"))
    # AI Backtest Lab 기본 레버리지는 1배. 사용자가 지정하면 반영.
    sanitized["leverage"] = _normalize_leverage(params.get("leverage"), default=1)
    # AI Backtest Lab는 저장된 데이터(CSV) 기준으로 고정 실행
    sanitized["use_csv"] = True
    return sanitized


def _minimal_backtest_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "coin": params["coin"],
        "interval": params["interval"],
        "strategy_id": params["strategy_id"],
        "direction": params["direction"],
        "leverage": _normalize_leverage(params.get("leverage"), default=1),
        "use_csv": True,
    }


def _normalize_gemini_model(model: str) -> str:
    """잘못된 또는 deprecated Gemini 모델명을 사용 가능한 모델로 치환."""
    if not model or not model.strip():
        return GEMINI_DEFAULT_MODEL
    key = model.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in key:
        key = key.replace("--", "-")
    if key in GEMINI_MODEL_ALIASES:
        return GEMINI_MODEL_ALIASES[key]
    # gemini-3 계열 중 미확인 하위 모델명은 기본 모델로 강등
    if key.startswith("gemini-3"):
        return GEMINI_DEFAULT_MODEL
    return key


def _validate_gemini_key(api_key: str) -> Optional[str]:
    """Gemini REST API 키 형식 사전 검증."""
    key = (api_key or "").strip()
    if not key:
        return "API key is empty."
    if key.startswith("gen-lang-client-"):
        return (
            "Invalid key format: 'gen-lang-client-...' is a browser client key, not a Gemini REST API key. "
            "Use an AI Studio key (usually starts with 'AIza')."
        )
    return None

def _call_gemini(
    api_key: str,
    prompt: str,
    model: str = GEMINI_DEFAULT_MODEL,
    history: Optional[list] = None,
    temperature: float = 0.2,
) -> AIServiceResult:
    """Google Gemini API 호출 래퍼. 내부 전송은 llm client adapter를 사용."""
    model = _normalize_gemini_model(model)

    # 전략 목록을 프롬프트에 주입
    strat_ids = [s['id'] for s in STRATS]
    full_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(strategy_list=", ".join(strat_ids))

    client = build_llm_client(
        "gemini",
        api_key=api_key,
        model=model,
        # Keep this injection so existing tests can monkeypatch ai_service.requests.post.
        http_post=requests.post,
    )
    llm_result = client.generate(
        system_prompt=full_system_prompt,
        prompt=prompt,
        history=history,
        temperature=temperature,
    )

    error = llm_result.get("error")
    error_code = llm_result.get("error_code")
    if error is not None:
        if error_code == ERROR_CODE_MODEL_HTTP:
            logger.error("Gemini API HTTP error (model=%s): %s", model, error)
        elif error_code == ERROR_CODE_MODEL_NETWORK:
            logger.error("Gemini API request error (model=%s): %s", model, error)
        elif error_code == ERROR_CODE_MODEL_RESPONSE_FORMAT:
            logger.error("Gemini API unexpected parse error (model=%s): %s", model, error)
        return {
            "thought": f"Error calling AI ({model}): {error}",
            "params": None,
            "error": error,
            "error_code": error_code,
        }

    text = str(llm_result.get("text") or "")
    parsed = _extract_json_from_text(text)
    if parsed is None:
        # JSON 형식이 아니면 자연어 답변으로 처리 (기본 동작)
        return {
            "thought": text.strip(),
            "params": None,
            "error": None,
            "error_code": None,
        }
    return {
        "thought": parsed.get("thought", ""),
        "params": parsed.get("params"),
        "error": None,
        "error_code": None,
    }

def process_ai_research(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = GEMINI_DEFAULT_MODEL,
    provider: str = "gemini",
    history: Optional[list] = None,
    temperature: float = 0.2,
) -> AIServiceResult:
    """AI 파라미터 추출 및 백테스트 실행"""
    provider_norm = (provider or "gemini").strip().lower()
    if provider_norm != "gemini":
        msg = f"Provider '{provider_norm}' is not supported yet. Use provider='gemini'."
        return _build_ai_result(
            answer=msg,
            execution_path="provider_validation",
            error=msg,
            error_code=ERROR_CODE_PROVIDER_UNSUPPORTED,
        )

    effective_api_key = api_key or settings.GEMINI_API_KEY
    if not effective_api_key:
        msg = "Gemini API key is missing. Please provide it in the request or set GEMINI_API_KEY environment variable."
        return _build_ai_result(
            answer=msg,
            execution_path="api_key_validation",
            error="API key is missing.",
            error_code=ERROR_CODE_API_KEY_INVALID,
        )

    clean_prompt, ui_context = _split_prompt_and_ui_context(prompt)
    is_optimization_request = _looks_like_optimization_request(clean_prompt)
    prompt_leverage = _extract_leverage_from_prompt(clean_prompt)
    normalized_model = _normalize_gemini_model(model)
    cache_key = _build_ai_cache_key(
        clean_prompt=clean_prompt,
        ui_context=ui_context,
        provider=provider_norm,
        model=normalized_model,
        temperature=temperature,
        history=history,
    )

    cached = AI_RESPONSE_CACHE.get(cache_key)
    if isinstance(cached, dict):
        execution_path = str(cached.get("execution_path") or "cached")
        return _normalize_result_payload(cached, execution_path=execution_path, cache_hit=True)

    if is_optimization_request and _contains_probability_intent(clean_prompt):
        optimization_clarification = _build_optimization_clarification_payload(clean_prompt, ui_context)
        AI_RESPONSE_CACHE.set(cache_key, optimization_clarification)
        return _normalize_result_payload(
            optimization_clarification,
            execution_path="optimization_clarification",
            cache_hit=False,
        )

    if _looks_ambiguous_prompt(clean_prompt) and not is_optimization_request:
        clarification = _build_clarification_payload(clean_prompt, ui_context)
        AI_RESPONSE_CACHE.set(cache_key, clarification)
        return _normalize_result_payload(
            clarification,
            execution_path="clarification",
            cache_hit=False,
        )

    probability_result = _run_conditional_probability_analysis(clean_prompt, ui_context)
    if probability_result is not None:
        normalized_probability = _normalize_result_payload(
            probability_result,
            execution_path="conditional_probability",
            cache_hit=False,
        )
        if normalized_probability.get("error") is None:
            AI_RESPONSE_CACHE.set(cache_key, normalized_probability)
        return normalized_probability

    key_error = _validate_gemini_key(effective_api_key)
    if key_error:
        return _build_ai_result(
            answer=key_error,
            execution_path="api_key_validation",
            error=key_error,
            error_code=ERROR_CODE_API_KEY_INVALID,
        )

    # 1. LLM 호출
    ai_response = _call_gemini(
        api_key=effective_api_key,
        prompt=prompt,
        model=normalized_model,
        history=history,
        temperature=temperature,
    )
    thought = ai_response.get("thought", "Analysis failed.")
    raw_params = ai_response.get("params")
    if raw_params is not None:
        params_dict = _sanitize_backtest_params(raw_params)
        if prompt_leverage is not None:
            params_dict["leverage"] = prompt_leverage
    elif is_optimization_request and ai_response.get("error") is None:
        optimization_clarification = _build_optimization_clarification_payload(clean_prompt, ui_context)
        AI_RESPONSE_CACHE.set(cache_key, optimization_clarification)
        return _normalize_result_payload(
            optimization_clarification,
            execution_path="optimization_clarification",
            cache_hit=False,
        )
    else:
        params_dict = None
    ai_error = ai_response.get("error")
    ai_error_code = ai_response.get("error_code")
    
    backtest_result = None
    final_analysis_result = None
    
    # 2. 파라미터가 성공적으로 추출되었다면 백테스트 실행
    if params_dict is not None:
        try:
            try:
                bt_params = BacktestParams(**params_dict)
            except Exception as validation_error:
                logger.warning(
                    "Invalid AI backtest params detected. Falling back to minimal safe params. error=%s raw=%s",
                    validation_error,
                    params_dict,
                )
                params_dict = _minimal_backtest_params(params_dict)
                bt_params = BacktestParams(**params_dict)
                thought += "\n(Invalid AI params were normalized to safe defaults.)"

            # 3. 최적화 요청이면 탐색 후 최적 결과를 반영, 아니면 단일 백테스트 실행
            logger.info("AI generated params: %s", bt_params)
            if is_optimization_request:
                optimization_payload = _run_backtest_parameter_optimization(bt_params, clean_prompt)
                if optimization_payload.get("error") is None:
                    params_dict = optimization_payload.get("params")
                    backtest_result = optimization_payload.get("backtest_result")
                    final_analysis_result = optimization_payload.get("analysis_result")
                    thought = f"{thought}\n\n{optimization_payload.get('answer', '')}".strip()
                else:
                    thought += (
                        "\n(Auto optimization failed, so a single backtest was executed.)"
                    )
                    backtest_result = run_backtest_service(bt_params)
            else:
                backtest_result = run_backtest_service(bt_params)
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            thought += f"\n(Backtest failed: {str(e)})"
            ai_error = str(e)
            ai_error_code = ERROR_CODE_BACKTEST_EXECUTION

    if ai_error is not None:
        execution_path = "llm_or_backtest_error"
    elif backtest_result is not None and is_optimization_request:
        execution_path = "llm_backtest_optimized"
    elif backtest_result is not None:
        execution_path = "llm_backtest"
    else:
        execution_path = "llm_text"

    final_result = _build_ai_result(
        answer=thought,
        backtest_params=params_dict,
        backtest_result=backtest_result,
        analysis_result=final_analysis_result,
        execution_path=execution_path,
        error=ai_error,
        error_code=ai_error_code,
    )
    if final_result.get("error") is None:
        AI_RESPONSE_CACHE.set(cache_key, final_result)
    return final_result
