"""Contract tests for trend-indicator service orchestration."""

from pathlib import Path
import sys

import pandas as pd


backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from modules.stats import service as stats_service


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

    monkeypatch.setattr(
        stats_service,
        "_load_data_for_analysis",
        lambda coin, interval, use_csv, total_candles=2000: source_df,
    )

    called = {"count": 0}

    def _mock_indicator_adapter(
        df: pd.DataFrame,
        mode: str = "backtest",
        prepare_kwargs=None,
    ) -> pd.DataFrame:
        called["count"] += 1
        out = df.copy()
        out["rsi"] = 51.0
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
        out["vwap_20"] = 109.0
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

    latest = result["data"]["latest"]
    assert latest["slow_stoch_20k"] == 35.0
    assert latest["slow_stoch_10k"] == 25.0
    assert latest["slow_stoch_5k"] == 15.0


def test_run_trend_indicators_analysis_uses_current_candle_for_all_latest(monkeypatch):
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
    out.loc[idx[1], "macd_hist"] = -1.0
    out.loc[idx[1], "adx"] = 12.0
    out.loc[idx[1], "slow_stoch_5k"] = 21.0
    out.loc[idx[1], "slow_stoch_5d"] = 22.0
    out.loc[idx[1], "slow_stoch_10k"] = 31.0
    out.loc[idx[1], "slow_stoch_10d"] = 32.0
    out.loc[idx[1], "slow_stoch_20k"] = 41.0
    out.loc[idx[1], "slow_stoch_20d"] = 42.0
    out.loc[idx[1], "vwap_20"] = 101.0
    out.loc[idx[1], "supertrend"] = 100.0
    out.loc[idx[1], "supertrend_dir"] = -1.0
    out.loc[idx[1], "sma20"] = 99.0
    out.loc[idx[1], "sma50"] = 98.0
    out.loc[idx[1], "sma200"] = 97.0

    # 현재 진행 봉 값 (서비스가 반드시 이 값을 latest로 내보내야 함)
    out.loc[idx[2], "rsi"] = 77.0
    out.loc[idx[2], "macd_hist"] = 3.0
    out.loc[idx[2], "adx"] = 44.0
    out.loc[idx[2], "slow_stoch_5k"] = 25.0
    out.loc[idx[2], "slow_stoch_5d"] = 26.0
    out.loc[idx[2], "slow_stoch_10k"] = 35.0
    out.loc[idx[2], "slow_stoch_10d"] = 36.0
    out.loc[idx[2], "slow_stoch_20k"] = 45.0
    out.loc[idx[2], "slow_stoch_20d"] = 46.0
    out.loc[idx[2], "vwap_20"] = 102.0
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
    assert latest["rsi"] == 77.0
    assert latest["macd_hist"] == 3.0
    assert latest["adx"] == 44.0
    assert latest["slow_stoch_5k"] == 25.0
    assert latest["slow_stoch_10k"] == 35.0
    assert latest["slow_stoch_20k"] == 45.0
    assert latest["vwap_20"] == 102.0
    assert latest["supertrend"] == 101.0
    assert latest["supertrend_dir"] == 1.0
    assert latest["sma20"] == 100.0
    assert latest["sma50"] == 99.0
    assert latest["sma200"] == 98.0

    # 시계열도 현재 봉을 포함해야 한다.
    assert result["data"]["series"]["rsi"]["t"][-1] == str(idx[2])
    assert result["data"]["series"]["slow_stoch_5k"]["v"][-1] == 25.0
