"""Scanner API service layer."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from core.indicators import prepare_strategy_data
from core.presets import load_presets
from core.strategies import STRATS
from models.request import PatternScanParams, ScannerParams
from services.pattern_logic import compute_pattern_stats, detect_patterns
from utils.data_loader import load_data_for_analysis


def _find_strategy(strategy_id: str) -> Dict[str, Any] | None:
    return next((s for s in STRATS if s["id"] == strategy_id), None)


def run_pattern_scanner_service(params: PatternScanParams) -> Dict[str, Any]:
    """Run pattern scanner for multiple intervals."""
    tf_stats: Dict[str, Any] = {}

    for interval in params.intervals:
        try:
            df, _ = load_data_for_analysis(
                params.coin,
                interval,
                params.use_csv,
                total_candles=500,
            )
        except ValueError:
            continue

        patterns = detect_patterns(df)
        stats = compute_pattern_stats(
            df,
            patterns,
            params.horizon,
            params.tp_pct / 100.0,
            params.mode,
            params.position,
        )
        tf_stats[interval] = stats

    return {
        "success": True,
        "data": tf_stats,
        "mode": params.mode,
        "position": params.position,
    }


def _build_strategy_signals(last_row: pd.Series, target_strats: List[str]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []

    for strat in STRATS:
        if strat["id"] not in target_strats:
            continue

        prefix = strat["prefix"]
        long_sig = bool(last_row.get(f"{prefix}_Long", False))
        short_sig = bool(last_row.get(f"{prefix}_Short", False))

        signals.append(
            {
                "id": strat["id"],
                "name_ko": strat["name_ko"],
                "name_en": strat["name_en"],
                "long_signal": long_sig,
                "short_signal": short_sig,
            }
        )

    return signals


def _build_market_context(last_row: pd.Series) -> Dict[str, Any]:
    return {
        "last_time": str(last_row["open_dt"]),
        "last_close": float(last_row["close"]),
        "regime": str(last_row.get("Regime", "Unknown")),
        "adx": float(last_row.get("ADX", 0)),
        "rsi": float(last_row.get("RSI", 50)),
    }


def _build_preset_signals(df: pd.DataFrame) -> List[Dict[str, Any]]:
    preset_signals: List[Dict[str, Any]] = []
    presets = load_presets()

    for name, cfg in presets.items():
        params = cfg.get("params", {})

        df_preset = prepare_strategy_data(
            df,
            rsi_ob_level=params.get("rsi_ob", 70),
            sma_main_len=params.get("sma_main_len", params.get("ema_len", 200)),
            sma1_len=params.get("sma1_len", 20),
            sma2_len=params.get("sma2_len", 60),
            adx_threshold=params.get("adx_thr", 25),
            donch_lookback=params.get("donch", 20),
            bb_length=params.get("bb_length", 20),
            bb_std_mult=params.get("bb_std_mult", 2.0),
            atr_length=params.get("atr_length", 20),
            kc_mult=params.get("kc_mult", 1.5),
            vol_ma_length=params.get("vol_ma_len", 20),
            vol_spike_k=params.get("vol_spike_k", 2.0),
            macd_fast=params.get("macd_fast", 12),
            macd_slow=params.get("macd_slow", 26),
            macd_signal=params.get("macd_signal", 9),
        )

        last_preset = df_preset.iloc[-1]
        strat_id = cfg.get("strat_id")
        strat_info = _find_strategy(strat_id)
        if strat_info is None:
            continue

        prefix = strat_info["prefix"]
        long_sig = bool(last_preset.get(f"{prefix}_Long", False))
        short_sig = bool(last_preset.get(f"{prefix}_Short", False))

        preset_signals.append(
            {
                "name": name,
                "strategy_id": strat_id,
                "long_signal": long_sig,
                "short_signal": short_sig,
            }
        )

    return preset_signals


def run_scanner_service(params: ScannerParams) -> Dict[str, Any]:
    """Scan multiple strategies for current signals."""
    df, _ = load_data_for_analysis(
        params.coin,
        params.interval,
        params.use_csv,
        total_candles=600,
    )
    df = prepare_strategy_data(df)
    last_row = df.iloc[-1]

    target_strats = params.strategies if params.strategies else [s["id"] for s in STRATS]
    signals = _build_strategy_signals(last_row, target_strats)
    market_context = _build_market_context(last_row)
    preset_signals = _build_preset_signals(df)

    return {
        "success": True,
        "signals": signals,
        "preset_signals": preset_signals,
        "market_context": market_context,
    }
