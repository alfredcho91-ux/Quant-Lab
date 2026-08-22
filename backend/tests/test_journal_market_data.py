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


def test_journal_market_data_prefers_deepcoin_for_deepcoin_positions(monkeypatch):
    native = _candles()
    monkeypatch.setattr(market_data, "fetch_deepcoin_swap_klines", lambda *args, **kwargs: native)
    monkeypatch.setattr(market_data, "fetch_binance_klines", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("fallback should not run")))

    frame = market_data.load_journal_ohlcv("BTC/USDT", "4h", total_candles=100, exchange="Deepcoin")

    assert frame is not None
    assert market_data.market_source(frame) == market_data.DEEPCOIN_SOURCE
    assert market_data.is_market_fallback(frame) is False


def test_journal_market_data_marks_binance_as_fallback_when_native_is_unavailable(monkeypatch):
    monkeypatch.setattr(market_data, "fetch_deepcoin_swap_klines", lambda *args, **kwargs: None)
    monkeypatch.setattr(market_data, "fetch_binance_klines", lambda *args, **kwargs: _candles())

    frame = market_data.load_journal_ohlcv("BTC/USDT", "2h", total_candles=100, exchange="Deepcoin")

    assert frame is not None
    assert market_data.market_source(frame) == market_data.BINANCE_FALLBACK_SOURCE
    assert market_data.is_market_fallback(frame) is True


def test_weekly_native_candles_use_the_next_open_as_the_completed_close_time():
    week_ms = 7 * 24 * 60 * 60 * 1000
    frame = market_data._normalize_deepcoin_rows([
        [1_000, "100", "101", "99", "100.5", "10", "1000"],
        [1_000 + week_ms, "101", "102", "100", "101.5", "11", "1100"],
    ], "1w")

    assert frame is not None
    assert int(frame.iloc[0]["close_time"]) == 1_000 + week_ms - 1
