"""Backtest domain router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.modules.backtest.schemas import BacktestEnvelope, BacktestParams
from backend.modules.backtest.service import run_backtest_service
from backend.utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest", response_model=BacktestEnvelope)
@handle_api_errors(include_traceback=False)
async def api_backtest(params: BacktestParams):
    """Run backtest with given parameters."""
    return await run_in_threadpool(run_backtest_service, params)
