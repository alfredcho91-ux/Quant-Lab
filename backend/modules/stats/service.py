"""Stats API service layer.

This module centralizes orchestration logic that was previously embedded
directly in routes/stats.py so route handlers stay thin.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from core.indicators import build_indicator_adapter
from strategy.bb_mid import (
    add_bb_indicators,
    analyze_bb_mid_touch,
    collect_event_returns,
)
from strategy.combo_filter import analyze_combo_filter
from strategy.hybrid import analyze_hybrid_strategy, analyze_live_mode, run_hybrid_backtest
from utils.data_loader import load_data_for_analysis
from utils.stats import safe_float


def _load_data_for_analysis(
    coin: str,
    interval: str,
    use_csv: bool,
    total_candles: int = 2000,
):
    """Common data loading wrapper used across stats endpoints."""
    try:
        df, _ = load_data_for_analysis(coin, interval, use_csv, total_candles=total_candles)
        return df
    except ValueError:
        return None


def _get_optimal_candle_count(interval: str) -> int:
    """Get optimal candle count by timeframe for BB mid analysis."""
    counts = {
        "15m": 3000,
        "30m": 2500,
        "1h": 2000,
        "2h": 1500,
        "4h": 1000,
        "8h": 750,
        "12h": 500,
        "1d": 1000,
        "3d": 500,
        "1w": 500,
        "1M": 200,
    }
    return counts.get(interval, 2000)


def run_bb_mid_analysis(
    coin: str,
    intervals: List[str],
    start_side: str,
    max_bars: int,
    regime: Optional[str],
    use_csv: bool,
) -> Dict[str, Any]:
    """Calculate BB mid touch analysis for multiple intervals."""
    results = []
    excursions: Dict[str, Dict[str, float]] = {}

    for interval in intervals:
        candle_count = _get_optimal_candle_count(interval)
        df = _load_data_for_analysis(coin, interval, use_csv, candle_count)

        if df is None or df.empty:
            results.append(
                {
                    "interval": interval,
                    "events": 0,
                    "success": 0,
                    "success_rate": None,
                    "error": "No data",
                }
            )
            continue

        df = add_bb_indicators(df)
        stats = analyze_bb_mid_touch(
            df=df,
            start_side=start_side,
            max_bars=max_bars,
            regime=regime,
        )

        if stats["events"] > 0:
            event_returns = collect_event_returns(
                df=df,
                start_side=start_side,
                max_bars=max_bars,
                regime=regime,
            )

            mfe_list = event_returns.get("mfe", [])
            mae_list = event_returns.get("mae", [])
            end_list = event_returns.get("end", [])

            if mfe_list and mae_list and end_list:
                excursions[interval] = {
                    "avg_mfe": float(np.mean(mfe_list)),
                    "avg_mae": float(np.mean(mae_list)),
                    "avg_end": float(np.mean(end_list)),
                }

        results.append(
            {
                "interval": interval,
                "events": stats["events"],
                "success": stats["success"],
                "success_rate": stats["success_rate"],
                "avg_bars_to_mid": stats.get("avg_bars_to_mid"),
            }
        )

    return {
        "success": True,
        "data": results,
        "excursions": excursions,
        "start_side": start_side,
    }


def run_combo_filter_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run combo filter analysis with loaded market data."""
    coin = params.get("coin", "BTC")
    interval = params.get("interval", "1h")
    use_csv = params.get("use_csv", False)

    df = _load_data_for_analysis(coin, interval, use_csv)
    if df is None:
        return {"success": False, "error": "Failed to load data"}

    stats = analyze_combo_filter(params, df)
    return {"success": True, "data": stats}


def run_trend_indicators_analysis(coin: str, interval: str, use_csv: bool) -> Dict[str, Any]:
    """Compute latest/chart trend indicators for Trend Judgment (Slow Stochastic profile)."""
    df = _load_data_for_analysis(coin, interval, use_csv, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}

    indicators_df = build_indicator_adapter(df, mode="trend_judgment")
    # 진행 중인 최신 봉 기준으로 표시한다.
    idx = -1
    row = indicators_df.iloc[idx]

    def _row_value(canonical: str, legacy: str) -> Optional[float]:
        value = row.get(canonical)
        if value is None or (isinstance(value, (float, np.floating)) and np.isnan(value)):
            value = row.get(legacy)
        return safe_float(value)

    slow_5k = _row_value("slow_stoch_5k", "stoch_rsi_5k")
    slow_5d = _row_value("slow_stoch_5d", "stoch_rsi_5d")
    slow_10k = _row_value("slow_stoch_10k", "stoch_rsi_10k")
    slow_10d = _row_value("slow_stoch_10d", "stoch_rsi_10d")
    slow_20k = _row_value("slow_stoch_20k", "stoch_rsi_20k")
    slow_20d = _row_value("slow_stoch_20d", "stoch_rsi_20d")

    latest = {
        "close": safe_float(row.get("close")),
        "rsi": safe_float(row.get("rsi")),
        "macd_hist": safe_float(row.get("macd_hist")),
        "adx": safe_float(row.get("adx")),
        "atr": safe_float(row.get("atr")),
        "atr_pct": safe_float(row.get("atr_pct")),
        "sma20": safe_float(row.get("sma20")),
        "sma50": safe_float(row.get("sma50")),
        "sma200": safe_float(row.get("sma200")),
        "slow_stoch_5k": slow_5k,
        "slow_stoch_5d": slow_5d,
        "slow_stoch_10k": slow_10k,
        "slow_stoch_10d": slow_10d,
        "slow_stoch_20k": slow_20k,
        "slow_stoch_20d": slow_20d,
        "vwap_20": safe_float(row.get("vwap_20")),
        "supertrend": safe_float(row.get("supertrend")),
        "supertrend_dir": safe_float(row.get("supertrend_dir")),
    }

    chart_len = min(200, len(indicators_df))
    chart_df = indicators_df.iloc[-chart_len:]
    series = {}

    def _series_payload(canonical: str, legacy: Optional[str] = None) -> Optional[Dict[str, List[Any]]]:
        source_col = canonical
        if source_col not in chart_df.columns and legacy and legacy in chart_df.columns:
            source_col = legacy
        if source_col not in chart_df.columns:
            return None
        s = chart_df[source_col].dropna()
        return {"t": s.index.astype(str).tolist(), "v": s.tolist()}

    plain_series_columns = ["close", "rsi", "macd_hist", "atr_pct", "vwap_20", "supertrend"]
    for col in plain_series_columns:
        payload = _series_payload(col)
        if payload is not None:
            series[col] = payload

    slow_mappings = [
        ("slow_stoch_5k", "stoch_rsi_5k"),
        ("slow_stoch_5d", "stoch_rsi_5d"),
        ("slow_stoch_10k", "stoch_rsi_10k"),
        ("slow_stoch_10d", "stoch_rsi_10d"),
        ("slow_stoch_20k", "stoch_rsi_20k"),
        ("slow_stoch_20d", "stoch_rsi_20d"),
    ]
    for canonical, legacy in slow_mappings:
        payload = _series_payload(canonical, legacy)
        if payload is None:
            continue
        series[canonical] = payload

    return {
        "success": True,
        "data": {
            "latest": latest,
            "series": series,
            "interval": interval,
            "coin": coin,
        },
    }


def run_hybrid_analysis_service(
    coin: str,
    interval: str,
    strategies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Analyze hybrid strategy signals."""
    df = _load_data_for_analysis(coin, interval, use_csv=False, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}

    return analyze_hybrid_strategy(
        df=df,
        coin=coin,
        interval=interval,
        strategies=strategies,
    )


def run_hybrid_backtest_service(
    coin: str,
    interval: str,
    strategy: str,
    tp: float,
    sl: float,
    max_hold: int,
) -> Dict[str, Any]:
    """Run hybrid strategy backtest."""
    df = _load_data_for_analysis(coin, interval, use_csv=False, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}

    return run_hybrid_backtest(
        df=df,
        coin=coin,
        interval=interval,
        strategy=strategy,
        tp=tp,
        sl=sl,
        max_hold=max_hold,
    )


def run_hybrid_live_service(
    coin: str,
    interval: str,
    strategies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Analyze hybrid strategy in live mode."""
    df = _load_data_for_analysis(coin, interval, use_csv=False, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}

    return analyze_live_mode(
        df=df,
        coin=coin,
        interval=interval,
        strategies=strategies,
    )
