"""Tests for EMA 200 filters in streak analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from strategy import analyze_streak_pattern, clear_cache
from strategy import streak as streak_module
from strategy.context import AnalysisContext
from strategy.streak.common import prepare_dataframe
from strategy.streak.cache_ops import indicators_cache
from strategy.streak.complex_strategy import run_complex_analysis
from strategy.streak.data_ops import (
    calculate_indicators,
    filter_rows_by_ema_200_position,
    get_or_calculate_indicators,
)
from strategy.streak.simple_strategy import run_simple_analysis


def _build_price_df(
    periods: int,
    *,
    trend: str,
    pattern: list[int] | None = None,
    freq: str = "D",
) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq=freq)
    rows = []

    for i, date in enumerate(dates):
        if trend == "up":
            base_price = 100 + (i * 2.0)
        else:
            base_price = 1000 - (i * 2.0)

        direction = pattern[i % len(pattern)] if pattern else 1
        if direction == 1:
            open_price = base_price
            close_price = base_price + 0.8
        else:
            open_price = base_price + 0.8
            close_price = base_price

        rows.append(
            {
                "date": date,
                "open": open_price,
                "high": max(open_price, close_price) + 0.4,
                "low": min(open_price, close_price) - 0.4,
                "close": close_price,
                "volume": 1000 + i,
            }
        )

    return pd.DataFrame(rows).set_index("date")


def test_filter_rows_by_ema_200_position_respects_trend_direction():
    uptrend = calculate_indicators(_build_price_df(260, trend="up"))
    downtrend = calculate_indicators(_build_price_df(260, trend="down"))

    up_rows = uptrend.iloc[-10:].copy()
    down_rows = downtrend.iloc[-10:].copy()

    assert len(filter_rows_by_ema_200_position(uptrend, up_rows, "above")) == len(up_rows)
    assert len(filter_rows_by_ema_200_position(uptrend, up_rows, "below")) == 0
    assert len(filter_rows_by_ema_200_position(downtrend, down_rows, "below")) == len(down_rows)
    assert len(filter_rows_by_ema_200_position(downtrend, down_rows, "above")) == 0


def test_filter_rows_by_ema_200_position_uses_original_close_when_heikin_ashi_is_enabled():
    index = pd.date_range("2024-01-01", periods=2, freq="D")
    df = pd.DataFrame(
        {
            "close": [90.0, 91.0],
            "source_close": [110.0, 111.0],
            "ema_200": [100.0, 100.0],
        },
        index=index,
    )
    rows = df.copy()

    filtered = filter_rows_by_ema_200_position(df, rows, "above")

    assert len(filtered) == len(rows)


def test_calculate_indicators_uses_daily_ema_200_on_intraday_data():
    intraday = _build_price_df(1560, trend="up", freq="4h")
    with_indicators = calculate_indicators(intraday)

    expected_daily_ema = (
        intraday["close"]
        .resample("1D")
        .last()
        .dropna()
        .ewm(span=200, adjust=False)
        .mean()
        .reindex(intraday.index.normalize())
        .to_numpy()
    )
    actual_ema = with_indicators["ema_200"].to_numpy()

    assert np.allclose(actual_ema, expected_daily_ema, equal_nan=True)


def test_prepare_dataframe_supports_heikin_ashi_candles():
    source = pd.DataFrame(
        [
            {"date": "2024-01-01", "open": 10.0, "high": 13.0, "low": 9.0, "close": 12.0, "volume": 1000},
            {"date": "2024-01-02", "open": 12.0, "high": 15.0, "low": 11.0, "close": 14.0, "volume": 1001},
        ]
    ).assign(date=lambda df: pd.to_datetime(df["date"])).set_index("date")

    prepared = prepare_dataframe(source, direction="green", candle_mode="heikin_ashi")

    assert prepared.iloc[0]["open"] == 11.0
    assert prepared.iloc[0]["close"] == 11.0
    assert prepared.iloc[1]["open"] == 11.0
    assert prepared.iloc[1]["close"] == 13.0
    assert prepared.iloc[1]["is_green"]
    assert round(float(prepared.iloc[1]["body_pct"]), 2) == 18.18


def test_heikin_ashi_mode_keeps_indicator_values_on_original_ohlc():
    indicators_cache.clear()
    base_df = _build_price_df(260, trend="up", pattern=[1, -1])

    standard_df = prepare_dataframe(base_df, direction="green", candle_mode="standard")
    heikin_ashi_df = prepare_dataframe(base_df, direction="green", candle_mode="heikin_ashi")

    standard = get_or_calculate_indicators("CACHE_TEST", "1d", standard_df, "standard")
    heikin_ashi = get_or_calculate_indicators("CACHE_TEST", "1d", heikin_ashi_df, "heikin_ashi")

    assert not np.allclose(standard["close"].to_numpy(), heikin_ashi["close"].to_numpy(), equal_nan=True)
    assert np.allclose(standard["rsi"].to_numpy(), heikin_ashi["rsi"].to_numpy(), equal_nan=True)
    assert np.allclose(standard["atr_pct"].to_numpy(), heikin_ashi["atr_pct"].to_numpy(), equal_nan=True)
    assert np.allclose(standard["disparity"].to_numpy(), heikin_ashi["disparity"].to_numpy(), equal_nan=True)
    assert np.allclose(standard["ema_200"].to_numpy(), heikin_ashi["ema_200"].to_numpy(), equal_nan=True)


def test_analyze_streak_pattern_changes_results_when_candle_mode_switches(monkeypatch):
    rows = []
    for i in range(40):
        base = 100 + i * 1.5
        if i % 2 == 0:
            open_price = base
            close_price = base + 3
        else:
            open_price = base + 3
            close_price = base + 1

        rows.append(
            {
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "open": open_price,
                "high": max(open_price, close_price) + 2,
                "low": min(open_price, close_price) - 2,
                "close": close_price,
                "volume": 1000 + i,
            }
        )

    df = pd.DataFrame(rows).set_index("date")
    monkeypatch.setattr(streak_module, "load_data", lambda coin, interval: (df.copy(), False))

    clear_cache()
    standard = analyze_streak_pattern(
        {
            "coin": "HA_E2E_TEST",
            "interval": "1d",
            "n_streak": 2,
            "direction": "green",
            "candle_mode": "standard",
        }
    )
    clear_cache()
    heikin_ashi = analyze_streak_pattern(
        {
            "coin": "HA_E2E_TEST",
            "interval": "1d",
            "n_streak": 2,
            "direction": "green",
            "candle_mode": "heikin_ashi",
        }
    )

    assert standard["success"] is True
    assert heikin_ashi["success"] is True
    assert standard["analysis_mode"]["parameters"]["candle_mode"] == "standard"
    assert heikin_ashi["analysis_mode"]["parameters"]["candle_mode"] == "heikin_ashi"
    assert standard["total_cases"] == 0
    assert heikin_ashi["total_cases"] > standard["total_cases"]
    assert heikin_ashi["continuation_rate"] != standard["continuation_rate"]


def test_run_simple_analysis_marks_filtered_out_when_ema_200_removes_all_cases():
    df = prepare_dataframe(_build_price_df(260, trend="down"), direction="green")
    context = AnalysisContext(
        coin="EMA_SIMPLE_FILTER_TEST",
        interval="1d",
        n_streak=3,
        direction="green",
        ema_200_position="above",
    )

    result = run_simple_analysis(df, context)

    assert result["success"] is True
    assert result["mode"] == "simple"
    assert result["total_cases"] == 0
    assert result["filter_status"]["status"] == "filtered_out"
    assert result["filter_status"]["ema_200_position"] == "above"
    assert result["filter_status"]["total_matches"] > 0


def test_run_complex_analysis_marks_filtered_out_when_ema_200_removes_all_cases():
    df = prepare_dataframe(
        _build_price_df(260, trend="down", pattern=[1, -1]),
        direction="green",
    )
    context = AnalysisContext(
        coin="EMA_COMPLEX_FILTER_TEST",
        interval="1d",
        n_streak=2,
        direction="green",
        use_complex_pattern=True,
        complex_pattern=[1, -1],
        ema_200_position="above",
    )

    result = run_complex_analysis(df, context)

    assert result["success"] is True
    assert result["mode"] == "complex"
    assert result["total_cases"] == 0
    assert result["filter_status"]["status"] == "filtered_out"
    assert result["filter_status"]["ema_200_position"] == "above"
    assert result["filter_status"]["total_matches"] > 0
