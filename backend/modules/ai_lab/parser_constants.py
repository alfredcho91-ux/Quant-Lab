"""Regex constants and token maps for AI lab prompt parsing."""

from __future__ import annotations

import re

CONTEXT_LINE_PATTERN = re.compile(r"^\s*([a-zA-Z_]+)\s*=\s*(.+?)\s*$")

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

BOLLINGER_INTENT_PATTERN = re.compile(
    r"볼린저\s*밴드|볼밴|bollinger(?:\s*band)?|(?<![A-Za-z0-9])bb(?![A-Za-z0-9])",
    re.IGNORECASE,
)
BOLLINGER_RELATION_ABOVE_TOKENS = ("위", "above", "over", "상회")
BOLLINGER_RELATION_BELOW_TOKENS = ("아래", "below", "under", "하회")
BOLLINGER_CROSS_TOKENS = ("돌파", "뚫", "breakout", "cross")

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


__all__ = [
    "CONTEXT_LINE_PATTERN",
    "INTERVAL_ALIASES",
    "MONTH_INTERVAL_PATTERNS",
    "INTERVAL_REGEX_PATTERNS",
    "INTERVAL_ALIAS_REGEX_PATTERNS",
    "KOR_INTERVAL_HINTS",
    "COMPARATOR_KEYWORD_TO_OP",
    "NUMERIC_INDICATOR_DEFS",
    "BOLLINGER_INTENT_PATTERN",
    "BOLLINGER_RELATION_ABOVE_TOKENS",
    "BOLLINGER_RELATION_BELOW_TOKENS",
    "BOLLINGER_CROSS_TOKENS",
    "STOCH_GOLDEN_TOKENS",
    "STOCH_DEAD_TOKENS",
    "STOCH_INTENT_TOKENS",
    "OPTIMIZATION_HINT_TOKENS",
]
