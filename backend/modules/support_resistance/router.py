"""Support resistance API router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from modules.support_resistance.schemas import (
    SupportResistancePathParams,
    SupportResistanceQueryParams,
)
from modules.support_resistance.service import run_support_resistance_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["support-resistance"])


@router.get("/support-resistance/{coin}/{interval}", operation_id="get_support_resistance_levels")
@handle_api_errors()
async def api_support_resistance(
    path: Annotated[SupportResistancePathParams, Depends()],
    query: Annotated[SupportResistanceQueryParams, Depends()],
):
    """Calculate support/resistance levels."""
    return await run_in_threadpool(
        run_support_resistance_service,
        path.coin,
        path.interval,
        query.lookback,
        query.tolerance_pct,
        query.min_touches,
        query.show_pivots,
        query.htf_option,
    )

