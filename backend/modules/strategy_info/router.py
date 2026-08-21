"""Strategy information API router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from backend.modules.strategy_info.schemas import (
    StrategiesEnvelope,
    StrategyInfoEnvelope,
    StrategyInfoQueryParams,
)
from backend.modules.strategy_info.service import run_strategies_service, run_strategy_info_service
from backend.utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["strategy"])


@router.get("/strategies", response_model=StrategiesEnvelope)
@handle_api_errors()
async def api_strategies():
    """Get the available backtesting strategy catalog."""
    return await run_in_threadpool(run_strategies_service)


@router.get("/strategy-info/{strategy_id}", response_model=StrategyInfoEnvelope)
@handle_api_errors()
async def api_strategy_info(
    strategy_id: str,
    query: Annotated[StrategyInfoQueryParams, Depends()],
):
    """Get strategy explanation."""
    return await run_in_threadpool(
        run_strategy_info_service,
        strategy_id,
        query.lang,
        query.rsi_ob,
        query.sma_main_len,
        query.sma1_len,
        query.sma2_len,
    )
