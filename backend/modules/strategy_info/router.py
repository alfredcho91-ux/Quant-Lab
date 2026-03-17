"""Strategy information API router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from modules.strategy_info.schemas import StrategyInfoQueryParams
from modules.strategy_info.service import run_strategy_info_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["strategy"])


@router.get("/strategy-info/{strategy_id}")
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

