"""Market API service layer."""

from __future__ import annotations

from typing import Any, Dict

from utils.data_loader import load_data_for_analysis
from utils.data_service import discover_timeframes, get_fear_and_greed_index, get_market_prices


def run_market_prices_service() -> Dict[str, Any]:
    """Build market prices payload for major coins."""
    prices = get_market_prices()
    if prices is None:
        return {"success": False, "data": None, "error": "Failed to fetch prices"}

    result: Dict[str, Dict[str, Any]] = {}
    for symbol, data in prices.items():
        coin = symbol.replace("/USDT", "")
        result[coin] = {
            "last": data.get("last", 0),
            "percentage": data.get("percentage", 0),
            "high": data.get("high", 0),
            "low": data.get("low", 0),
            "volume": data.get("quoteVolume", 0),
        }

    return {"success": True, "data": result}


def run_fear_greed_service() -> Dict[str, Any]:
    """Build fear-greed response payload."""
    fear_greed = get_fear_and_greed_index()
    if fear_greed is None:
        return {"success": False, "data": None}
    return {"success": True, "data": fear_greed}


def run_timeframes_service(coin: str) -> Dict[str, Any]:
    """Build available timeframes payload for one coin."""
    all_tfs, binance_tfs, csv_tfs = discover_timeframes(coin)
    return {
        "success": True,
        "data": {
            "all": all_tfs,
            "binance": list(binance_tfs),
            "csv": csv_tfs,
        },
    }


def run_ohlcv_service(
    coin: str,
    interval: str,
    use_csv: bool = False,
    limit: int = 3000,
) -> Dict[str, Any]:
    """Load OHLCV data and serialize to API payload."""
    df, source = load_data_for_analysis(coin, interval, use_csv, total_candles=limit)
    df_serialized = df.copy()
    df_serialized["open_dt"] = df_serialized["open_dt"].astype(str)
    data = df_serialized.to_dict(orient="records")

    return {
        "success": True,
        "data": data,
        "source": source,
        "count": len(data),
    }

