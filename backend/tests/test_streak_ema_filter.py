"""Tests for EMA 200 filters in streak analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from strategy.context import AnalysisContext
from strategy.streak.common import prepare_dataframe
from strategy.streak.complex_strategy import run_complex_analysis
from strategy.streak.data_ops import calculate_indicators, filter_rows_by_ema_200_position
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
