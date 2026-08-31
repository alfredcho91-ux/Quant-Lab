"""Contract tests for trend-indicator service orchestration."""

import pandas as pd

from backend.modules.stats import service as stats_service


def _mock_ohlcv(rows: int = 120) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=rows, freq="h")
    close = pd.Series(range(rows), index=idx, dtype=float) + 100.0
    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


def test_run_trend_indicators_analysis_uses_trend_judgment_pipeline(monkeypatch):
    source_df = _mock_ohlcv(rows=120)
    called = {"count": 0, "total_candles": None}

    def _mock_loader(coin, interval, use_csv, total_candles=2000):
        called["total_candles"] = total_candles
        return source_df

    monkeypatch.setattr(stats_service, "_load_data_for_analysis", _mock_loader)

    def _mock_indicator_adapter(
        df: pd.DataFrame,
        mode: str = "backtest",
        prepare_kwargs=None,
    ) -> pd.DataFrame:
        called["count"] += 1
        out = df.copy()
        out["rsi"] = 51.0
        out["macd"] = 2.0
        out["macd_signal"] = 1.0
        out["macd_hist"] = 1.25
        out["adx"] = 23.0
        out["sma20"] = 110.0
        out["sma50"] = 108.0
        out["sma200"] = 101.0
        out["slow_stoch_5k"] = 15.0
        out["slow_stoch_5d"] = 12.0
        out["slow_stoch_10k"] = 25.0
        out["slow_stoch_10d"] = 21.0
        out["slow_stoch_20k"] = 35.0
        out["slow_stoch_20d"] = 31.0
        out["stoch_rsi_k"] = 61.0
        out["stoch_rsi_d"] = 57.0
        out["supertrend"] = 107.0
        out["supertrend_dir"] = 1.0
        return out

    monkeypatch.setattr(
        stats_service,
        "build_indicator_adapter",
        _mock_indicator_adapter,
    )

    result = stats_service.run_trend_indicators_analysis("BTC", "1h", use_csv=False)

    assert result["success"] is True
    assert called["count"] == 1
    assert called["total_candles"] == stats_service.TREND_INDICATOR_CANDLES

    latest = result["data"]["latest"]
    assert latest["slow_stoch_20k"] == 35.0
    assert latest["slow_stoch_10k"] == 25.0
    assert latest["slow_stoch_5k"] == 15.0
    assert latest["macd"] == 2.0
    assert latest["macd_signal"] == 1.0
    assert latest["macd_cross"] is None
    assert latest["macd_hist_direction"] == "flat"
    assert latest["stoch_rsi_k"] == 61.0
    assert latest["stoch_rsi_d"] == 57.0


def test_run_trend_indicators_analysis_uses_previous_completed_candle_for_all_latest(monkeypatch):
    source_df = _mock_ohlcv(rows=3)

    monkeypatch.setattr(
        stats_service,
        "_load_data_for_analysis",
        lambda coin, interval, use_csv, total_candles=2000: source_df,
    )

    idx = source_df.index
    out = source_df.copy()
    # 직전 봉 값
    out.loc[idx[1], "rsi"] = 11.0
    out.loc[idx[1], "macd"] = -0.5
    out.loc[idx[1], "macd_signal"] = 0.0
    out.loc[idx[1], "macd_hist"] = -1.0
    out.loc[idx[1], "adx"] = 12.0
    out.loc[idx[1], "slow_stoch_5k"] = 21.0
    out.loc[idx[1], "slow_stoch_5d"] = 22.0
    out.loc[idx[1], "slow_stoch_10k"] = 31.0
    out.loc[idx[1], "slow_stoch_10d"] = 32.0
    out.loc[idx[1], "slow_stoch_20k"] = 41.0
    out.loc[idx[1], "slow_stoch_20d"] = 42.0
    out.loc[idx[1], "stoch_rsi_k"] = 30.0
    out.loc[idx[1], "stoch_rsi_d"] = 35.0
    out.loc[idx[1], "supertrend"] = 100.0
    out.loc[idx[1], "supertrend_dir"] = -1.0
    out.loc[idx[1], "sma20"] = 99.0
    out.loc[idx[1], "sma50"] = 98.0
    out.loc[idx[1], "sma200"] = 97.0

    # 진행 중인 최신 봉 값 (서비스는 이 값을 화면에 내보내지 않아야 함)
    out.loc[idx[2], "rsi"] = 77.0
    out.loc[idx[2], "macd"] = 0.5
    out.loc[idx[2], "macd_signal"] = 0.0
    out.loc[idx[2], "macd_hist"] = 3.0
    out.loc[idx[2], "adx"] = 44.0
    out.loc[idx[2], "slow_stoch_5k"] = 25.0
    out.loc[idx[2], "slow_stoch_5d"] = 26.0
    out.loc[idx[2], "slow_stoch_10k"] = 35.0
    out.loc[idx[2], "slow_stoch_10d"] = 36.0
    out.loc[idx[2], "slow_stoch_20k"] = 45.0
    out.loc[idx[2], "slow_stoch_20d"] = 46.0
    out.loc[idx[2], "stoch_rsi_k"] = 65.0
    out.loc[idx[2], "stoch_rsi_d"] = 55.0
    out.loc[idx[2], "supertrend"] = 101.0
    out.loc[idx[2], "supertrend_dir"] = 1.0
    out.loc[idx[2], "sma20"] = 100.0
    out.loc[idx[2], "sma50"] = 99.0
    out.loc[idx[2], "sma200"] = 98.0

    monkeypatch.setattr(
        stats_service,
        "build_indicator_adapter",
        lambda df, mode="backtest", prepare_kwargs=None: out,
    )

    result = stats_service.run_trend_indicators_analysis("BTC", "1h", use_csv=False)

    latest = result["data"]["latest"]
    assert latest["rsi"] == 11.0
    assert latest["macd"] == -0.5
    assert latest["macd_signal"] == 0.0
    assert latest["macd_hist"] == -1.0
    assert latest["macd_cross"] is None
    assert latest["macd_hist_direction"] is None
    assert latest["adx"] == 12.0
    assert latest["slow_stoch_5k"] == 21.0
    assert latest["slow_stoch_10k"] == 31.0
    assert latest["slow_stoch_20k"] == 41.0
    assert latest["stoch_rsi_k"] == 30.0
    assert latest["stoch_rsi_d"] == 35.0
    assert latest["supertrend"] == 100.0
    assert latest["supertrend_dir"] == -1.0
    assert latest["sma20"] == 99.0
    assert latest["sma50"] == 98.0
    assert latest["sma200"] == 97.0

    # 시계열도 진행 중인 현재 봉을 제외해야 한다.
    assert result["data"]["series"]["rsi"]["t"][-1] == str(idx[1])
    assert result["data"]["series"]["volume"]["v"][-1] == 1000.0
    assert result["data"]["series"]["macd"]["v"][-1] == -0.5
    assert result["data"]["series"]["macd_signal"]["v"][-1] == 0.0
    assert result["data"]["series"]["slow_stoch_5k"]["v"][-1] == 21.0
    assert result["data"]["series"]["stoch_rsi_k"]["v"][-1] == 30.0


def test_run_trend_indicators_analysis_uses_open_dt_for_chart_timestamps(monkeypatch):
    source_df = _mock_ohlcv(rows=4).reset_index(names="open_dt")

    monkeypatch.setattr(
        stats_service,
        "_load_data_for_analysis",
        lambda coin, interval, use_csv, total_candles=2000: source_df,
    )

    def _mock_indicator_adapter(
        df: pd.DataFrame,
        mode: str = "backtest",
        prepare_kwargs=None,
    ) -> pd.DataFrame:
        out = df.copy()
        out["rsi"] = [35.0, 28.0, 72.0, 55.0]
        return out

    monkeypatch.setattr(stats_service, "build_indicator_adapter", _mock_indicator_adapter)

    result = stats_service.run_trend_indicators_analysis("BTC", "1h", use_csv=False)

    assert result["success"] is True
    assert result["data"]["series"]["rsi"]["t"] == [
        "2025-01-01 00:00:00",
        "2025-01-01 01:00:00",
        "2025-01-01 02:00:00",
    ]
