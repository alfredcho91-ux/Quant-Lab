"""Support resistance API router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from backend.modules.support_resistance.schemas import (
    SupportResistanceEnvelope,
    SupportResistancePathParams,
    SupportResistanceQueryParams,
)
from backend.modules.support_resistance.service import run_support_resistance_service
from backend.utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["support-resistance"])


@router.get(
    "/support-resistance/{coin}/{interval}",
    operation_id="get_support_resistance_levels",
    response_model=SupportResistanceEnvelope,
)
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
