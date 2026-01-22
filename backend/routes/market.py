# routes/market.py
"""시장 데이터 API 엔드포인트"""

from fastapi import APIRouter
import pandas as pd

from utils.data_service import get_market_prices, get_fear_and_greed_index, discover_timeframes, fetch_live_data
from utils.data_loader import load_data_for_analysis
from utils.decorators import handle_api_errors
from core.support_resistance import (
    build_sr_levels_from_swings,
    compute_daily_pivots,
    compute_htf_sr_levels,
)

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/market/prices")
@handle_api_errors()
async def api_market_prices():
    """Get current market prices for major coins"""
    prices = get_market_prices()
    if prices is None:
        return {"success": False, "data": None, "error": "Failed to fetch prices"}
    
    result = {}
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


@router.get("/market/fear-greed")
@handle_api_errors()
async def api_fear_greed():
    """Get Fear & Greed Index"""
    fng = get_fear_and_greed_index()
    if fng is None:
        return {"success": False, "data": None}
    return {"success": True, "data": fng}


@router.get("/timeframes/{coin}")
@handle_api_errors()
async def api_timeframes(coin: str):
    """Get available timeframes for a coin"""
    all_tfs, binance_tfs, csv_tfs = discover_timeframes(coin)
    return {
        "success": True,
        "data": {
            "all": all_tfs,
            "binance": list(binance_tfs),
            "csv": csv_tfs,
        }
    }


@router.get("/ohlcv/{coin}/{interval}")
@handle_api_errors()
async def api_ohlcv(coin: str, interval: str, use_csv: bool = False, limit: int = 3000):
    """Get OHLCV data for a coin and interval"""
    # Load data using common loader
    df, source = load_data_for_analysis(coin, interval, use_csv, total_candles=limit)
    
    # Convert to JSON-serializable format
    df["open_dt"] = df["open_dt"].astype(str)
    data = df.to_dict(orient="records")
    
    return {
        "success": True,
        "data": data,
        "source": source,
        "count": len(data),
    }


@router.get("/support-resistance/{coin}/{interval}")
@handle_api_errors()
async def api_support_resistance(
    coin: str,
    interval: str,
    lookback: int = 3,
    tolerance_pct: float = 0.3,
    min_touches: int = 3,
    show_pivots: bool = False,
    htf_option: str = "none",
):
    """Calculate support/resistance levels"""
    df = fetch_live_data(f"{coin}/USDT", interval, total_candles=1000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}
    
    frames = []
    
    # Swing-based SR levels
    sr_main = build_sr_levels_from_swings(
        df,
        lookback=lookback,
        tolerance_pct=tolerance_pct / 100.0,
        min_touches=min_touches,
        timeframe_label=interval,
    )
    if not sr_main.empty:
        frames.append(sr_main)
    
    # Daily pivots
    if show_pivots:
        pivots = compute_daily_pivots(df, last_n=1)
        if not pivots.empty:
            frames.append(pivots)
    
    # HTF levels
    if htf_option != "none":
        rule = "4H" if htf_option == "4H" else "1D"
        htf_levels = compute_htf_sr_levels(
            df,
            rule=rule,
            lookback=lookback,
            tolerance_pct=tolerance_pct / 100.0,
            min_touches=min_touches,
        )
        if not htf_levels.empty:
            frames.append(htf_levels)
    
    if frames:
        all_levels = pd.concat(frames, ignore_index=True)
        return {"success": True, "data": all_levels.to_dict(orient="records")}
    
    return {"success": True, "data": []}
