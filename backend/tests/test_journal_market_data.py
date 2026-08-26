import pandas as pd

from backend.modules.journal import market_data


def _candles() -> pd.DataFrame:
    return pd.DataFrame({
        "open_time": [1],
        "open": [100.0],
        "high": [101.0],
        "low": [99.0],
        "close": [100.5],
        "volume": [10.0],
        "quote_volume": [1_000.0],
        "close_time": [2],
        "trade_count": [1],
        "open_dt": pd.to_datetime([1], unit="ms", utc=True),
    })


def test_journal_market_data_always_uses_binance_usdt_m_futures(monkeypatch):
    captured = {}

    def fetch(symbol, interval, total_candles, end_time):
        captured.update({
            "symbol": symbol,
            "interval": interval,
            "total_candles": total_candles,
            "end_time": end_time,
        })
        return _candles()

    monkeypatch.setattr(market_data, "fetch_binance_klines", fetch)

    frame = market_data.load_journal_ohlcv(
        "BTC/USDT",
        "4h",
        total_candles=100,
        end_time=1_700_000_000_000,
        exchange="Deepcoin",
    )

    assert frame is not None
    assert captured == {
        "symbol": "BTCUSDT",
        "interval": "4h",
        "total_candles": 100,
        "end_time": 1_700_000_000_000,
    }
    assert market_data.market_source(frame) == market_data.BINANCE_USDT_M_FUTURES_SOURCE
    assert frame.attrs["market_source_fallback"] is False


def test_journal_market_data_returns_none_when_binance_usdt_m_is_unavailable(monkeypatch):
    monkeypatch.setattr(market_data, "fetch_binance_klines", lambda *args, **kwargs: None)

    assert market_data.load_journal_ohlcv("BTC/USDT", "2h", total_candles=100) is None
