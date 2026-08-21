from __future__ import annotations

import pandas as pd

from backend.utils import data_loader
from backend.utils import data_service


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open_time": [1_700_000_000_000, 1_700_000_060_000],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10.0, 12.0],
            "open_dt": pd.to_datetime([1_700_000_000_000, 1_700_000_060_000], unit="ms"),
        }
    )


def test_load_data_for_analysis_reuses_live_snapshot_cache(monkeypatch):
    calls = 0
    coin = "CACHE_BTC"
    interval = "1h"

    def fake_fetch(symbol: str, timeframe: str, limit: int = 1000, total_candles: int = 3000):
        nonlocal calls
        calls += 1
        assert symbol == f"{coin}/USDT"
        assert timeframe == interval
        assert total_candles == 120
        return _sample_frame()

    data_loader.LIVE_DATA_CACHE.clear()
    monkeypatch.setattr(data_loader, "fetch_live_data", fake_fetch)

    first_df, first_source = data_loader.load_data_for_analysis(
        coin,
        interval,
        use_csv=False,
        total_candles=120,
    )
    second_df, second_source = data_loader.load_data_for_analysis(
        coin,
        interval,
        use_csv=False,
        total_candles=120,
    )

    assert calls == 1
    assert first_source == "api"
    assert second_source == "api"
    assert first_df.equals(second_df)
    assert first_df is not second_df


def test_fetch_live_data_delegates_to_binance_rest_loader(monkeypatch):
    captured = {}
    expected = _sample_frame()

    def fake_fetch(symbol: str, timeframe: str, total_candles: int):
        captured.update(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "total_candles": total_candles,
            }
        )
        return expected

    monkeypatch.setattr(data_service, "fetch_binance_klines", fake_fetch)

    result = data_service.fetch_live_data("BTC/USDT", "4h", limit=500, total_candles=240)

    assert result is expected
    assert captured == {
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "total_candles": 240,
    }


def test_fetch_live_data_preserves_weekly_candle_cap(monkeypatch):
    captured = {}

    def fake_fetch(symbol: str, timeframe: str, total_candles: int):
        captured["total_candles"] = total_candles
        return _sample_frame()

    monkeypatch.setattr(data_service, "fetch_binance_klines", fake_fetch)

    data_service.fetch_live_data("BTC/USDT", "1w", total_candles=3_000)

    assert captured["total_candles"] == 300
