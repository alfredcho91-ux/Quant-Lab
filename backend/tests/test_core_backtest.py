"""Core backtest regression tests."""

import pandas as pd
import pytest

from core.backtest import run_backtest, summarize_trades


def _base_backtest_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [99.0, 100.0, 101.0, 102.0],
            "high": [100.0, 103.0, 102.0, 103.0],
            "low": [98.0, 99.2, 100.0, 101.0],
            "close": [99.0, 101.0, 101.0, 102.0],
            "open_dt": pd.date_range("2024-01-01 00:00:00", periods=4, freq="h"),
            "Regime": ["Bull", "Bull", "Bull", "Bull"],
            "Sig_Connors_Long": [True, False, False, False],
        }
    )


def test_run_backtest_uses_next_bar_open_for_entry():
    df = _base_backtest_df()
    trades = run_backtest(
        df=df,
        signal_col="Sig_Connors_Long",
        direction="Long",
        strategy_type="Fixed",
        tp_pct=0.02,
        sl_pct=0.01,
        max_bars=2,
        leverage=1,
        fee_entry_rate=0.0,
        fee_exit_rate=0.0,
    )

    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade["Entry Time"] == df.loc[1, "open_dt"]
    assert trade["Entry Price"] == pytest.approx(df.loc[1, "open"])
    assert trade["Outcome"] == "TP"
    assert trade["PnL"] == pytest.approx(0.02)


def test_run_backtest_raises_on_invalid_numeric_input():
    df = _base_backtest_df()
    df.loc[2, "high"] = float("nan")

    with pytest.raises(ValueError, match="Invalid OHLC values"):
        run_backtest(
            df=df,
            signal_col="Sig_Connors_Long",
            direction="Long",
            strategy_type="Fixed",
        )


def test_summarize_trades_supports_pnl_and_percent_columns():
    pnl_trades = pd.DataFrame({"PnL": [0.10, -0.05, 0.02]})
    summary = summarize_trades(pnl_trades)

    assert summary["n_trades"] == 3
    assert summary["win_rate"] == pytest.approx((2 / 3) * 100)
    assert summary["total_pnl"] == pytest.approx(((1.10 * 0.95 * 1.02) - 1) * 100)

    percent_trades = pd.DataFrame({"pnl_%": [10.0, -5.0]})
    summary_percent = summarize_trades(percent_trades)
    assert summary_percent["n_trades"] == 2
    assert summary_percent["total_pnl"] == pytest.approx(((1.10 * 0.95) - 1) * 100)


def test_run_backtest_long_liquidation_outcome():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [101.0, 101.0, 101.0, 101.0],
            "low": [99.0, 40.0, 99.0, 99.0],
            "close": [100.0, 100.0, 100.0, 100.0],
            "open_dt": pd.date_range("2024-01-01 00:00:00", periods=4, freq="h"),
            "Regime": ["Bull"] * 4,
            "Sig_Connors_Long": [True, False, False, False],
        }
    )

    trades = run_backtest(
        df=df,
        signal_col="Sig_Connors_Long",
        direction="Long",
        strategy_type="Fixed",
        tp_pct=0.05,
        sl_pct=0.02,
        max_bars=2,
        leverage=2,
        fee_entry_rate=0.0,
        fee_exit_rate=0.0,
    )

    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade["Outcome"] == "💀 Liquidation"
    assert trade["PnL"] == pytest.approx(-1.0)


def test_run_backtest_short_tp_outcome():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [101.0, 100.5, 100.5, 100.5],
            "low": [99.0, 97.0, 98.0, 99.0],
            "close": [100.0, 99.0, 99.0, 100.0],
            "open_dt": pd.date_range("2024-01-01 00:00:00", periods=4, freq="h"),
            "Regime": ["Bear"] * 4,
            "Sig_Connors_Short": [True, False, False, False],
        }
    )

    trades = run_backtest(
        df=df,
        signal_col="Sig_Connors_Short",
        direction="Short",
        strategy_type="Fixed",
        tp_pct=0.02,
        sl_pct=0.01,
        max_bars=2,
        leverage=1,
        fee_entry_rate=0.0,
        fee_exit_rate=0.0,
    )

    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade["Outcome"] == "TP"
    assert trade["PnL"] == pytest.approx(0.02)


def test_run_backtest_timeout_uses_close_price_when_no_tp_sl():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 101.0, 102.0],
            "high": [101.0, 101.0, 102.0, 103.0],
            "low": [99.0, 99.0, 100.0, 101.0],
            "close": [100.0, 100.0, 101.5, 102.0],
            "open_dt": pd.date_range("2024-01-01 00:00:00", periods=4, freq="h"),
            "Regime": ["Bull"] * 4,
            "Sig_Connors_Long": [True, False, False, False],
        }
    )

    trades = run_backtest(
        df=df,
        signal_col="Sig_Connors_Long",
        direction="Long",
        strategy_type="Fixed",
        tp_pct=0.5,
        sl_pct=0.5,
        max_bars=1,
        leverage=1,
        fee_entry_rate=0.0,
        fee_exit_rate=0.0,
    )

    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade["Outcome"] == "TimeOut"
    expected_raw_return = (101.5 - 100.0) / 100.0
    assert trade["PnL"] == pytest.approx(expected_raw_return)
