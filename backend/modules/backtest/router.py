"""Backtest domain router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from modules.backtest.schemas import AdvancedBacktestParams, BacktestParams
from modules.backtest.service import run_backtest_advanced_service, run_backtest_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest")
@handle_api_errors(include_traceback=False)
async def api_backtest(params: BacktestParams):
    """Run backtest with given parameters."""
    return await run_in_threadpool(run_backtest_service, params)


@router.post("/backtest-advanced")
@handle_api_errors(include_traceback=False)
async def api_backtest_advanced(params: AdvancedBacktestParams):
    """Run advanced backtest with train/test split and statistics."""
    return await run_in_threadpool(run_backtest_advanced_service, params)

