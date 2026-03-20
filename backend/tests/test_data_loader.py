from __future__ import annotations

import pandas as pd

from utils import data_loader


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
