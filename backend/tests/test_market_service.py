"""Tests for market service layer."""

import pandas as pd

from modules.market import service as market_service


def test_run_market_prices_service_success(monkeypatch):
    mock_prices = {
        "BTC/USDT": {
            "last": 100000,
            "percentage": 2.5,
            "high": 101000,
            "low": 98000,
            "quoteVolume": 12345,
        },
        "ETH/USDT": {
            "last": 5000,
            "percentage": -1.2,
            "high": 5100,
            "low": 4900,
            "quoteVolume": 23456,
        },
    }
    monkeypatch.setattr(market_service, "get_market_prices", lambda: mock_prices)

    result = market_service.run_market_prices_service()

    assert result["success"] is True
    assert result["data"]["BTC"]["last"] == 100000
    assert result["data"]["BTC"]["volume"] == 12345
    assert result["data"]["ETH"]["percentage"] == -1.2


def test_run_market_prices_service_failure(monkeypatch):
    monkeypatch.setattr(market_service, "get_market_prices", lambda: None)

    result = market_service.run_market_prices_service()

    assert result == {"success": False, "data": None, "error": "Failed to fetch prices"}


def test_run_fear_greed_service(monkeypatch):
    monkeypatch.setattr(market_service, "get_fear_and_greed_index", lambda: {"value": "70", "value_classification": "Greed"})
    success_result = market_service.run_fear_greed_service()
    assert success_result["success"] is True
    assert success_result["data"]["value"] == "70"

    monkeypatch.setattr(market_service, "get_fear_and_greed_index", lambda: None)
    failure_result = market_service.run_fear_greed_service()
    assert failure_result == {"success": False, "data": None}


def test_run_timeframes_service(monkeypatch):
    monkeypatch.setattr(
        market_service,
        "discover_timeframes",
        lambda coin: (["1h", "4h"], {"1h"}, ["4h"]),
    )

    result = market_service.run_timeframes_service("BTC")

    assert result["success"] is True
    assert result["data"]["all"] == ["1h", "4h"]
    assert sorted(result["data"]["binance"]) == ["1h"]
    assert result["data"]["csv"] == ["4h"]


def test_run_ohlcv_service(monkeypatch):
    df = pd.DataFrame(
        {
            "open_dt": pd.to_datetime(["2025-01-01 00:00:00", "2025-01-01 01:00:00"]),
            "open": [1.0, 2.0],
            "high": [1.2, 2.2],
            "low": [0.8, 1.8],
            "close": [1.1, 2.1],
            "volume": [10, 20],
        }
    )

    def _mock_loader(coin, interval, use_csv, total_candles):
        assert coin == "BTC"
        assert interval == "1h"
        assert use_csv is True
        assert total_candles == 2
        return df, "CSV file"

    monkeypatch.setattr(market_service, "load_data_for_analysis", _mock_loader)

    result = market_service.run_ohlcv_service("BTC", "1h", use_csv=True, limit=2)

    assert result["success"] is True
    assert result["source"] == "CSV file"
    assert result["count"] == 2
    assert isinstance(result["data"][0]["open_dt"], str)
