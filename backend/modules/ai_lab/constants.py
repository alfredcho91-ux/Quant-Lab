"""Shared constants for AI lab orchestration."""

from __future__ import annotations

import os

from services.ai_clients import (
    ERROR_CODE_MODEL_HTTP as CLIENT_ERROR_CODE_MODEL_HTTP,
    ERROR_CODE_MODEL_NETWORK as CLIENT_ERROR_CODE_MODEL_NETWORK,
    ERROR_CODE_MODEL_RESPONSE_EMPTY as CLIENT_ERROR_CODE_MODEL_RESPONSE_EMPTY,
    ERROR_CODE_MODEL_RESPONSE_FORMAT as CLIENT_ERROR_CODE_MODEL_RESPONSE_FORMAT,
)

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
    "gemini-3.0-pro-preivew": GEMINI_DEFAULT_MODEL,
    "gemini-3-pro-preview": GEMINI_DEFAULT_MODEL,
    "gemini-2.0-pro-exp-02-05": GEMINI_DEFAULT_MODEL,
}

ERROR_CODE_PROVIDER_UNSUPPORTED = "PROVIDER_UNSUPPORTED"
ERROR_CODE_API_KEY_INVALID = "API_KEY_INVALID"
ERROR_CODE_MODEL_HTTP = CLIENT_ERROR_CODE_MODEL_HTTP
ERROR_CODE_MODEL_NETWORK = CLIENT_ERROR_CODE_MODEL_NETWORK
ERROR_CODE_MODEL_RESPONSE_EMPTY = CLIENT_ERROR_CODE_MODEL_RESPONSE_EMPTY
ERROR_CODE_MODEL_RESPONSE_FORMAT = CLIENT_ERROR_CODE_MODEL_RESPONSE_FORMAT
ERROR_CODE_BACKTEST_EXECUTION = "BACKTEST_EXECUTION_ERROR"

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
