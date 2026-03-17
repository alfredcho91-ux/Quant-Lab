"""Market domain router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from modules.market.schemas import MarketCoinPathParams, MarketOHLCVPathParams, MarketOHLCVQueryParams
from modules.market.service import (
    run_fear_greed_service,
    run_market_prices_service,
    run_ohlcv_service,
    run_timeframes_service,
)
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/market/prices")
@handle_api_errors()
async def api_market_prices():
    """Get current market prices for major coins."""
    return await run_in_threadpool(run_market_prices_service)


@router.get("/market/fear-greed")
@handle_api_errors()
async def api_fear_greed():
    """Get Fear & Greed Index."""
    return await run_in_threadpool(run_fear_greed_service)


@router.get("/timeframes/{coin}")
@handle_api_errors()
async def api_timeframes(path: Annotated[MarketCoinPathParams, Depends()]):
    """Get available timeframes for a coin."""
    return await run_in_threadpool(run_timeframes_service, path.coin)


@router.get("/ohlcv/{coin}/{interval}")
@handle_api_errors()
async def api_ohlcv(
    path: Annotated[MarketOHLCVPathParams, Depends()],
    query: Annotated[MarketOHLCVQueryParams, Depends()],
):
    """Get OHLCV data for a coin and interval."""
    return await run_in_threadpool(
        run_ohlcv_service,
        path.coin,
        path.interval,
        query.use_csv,
        query.limit,
    )

