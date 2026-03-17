"""통계 분석 API 엔드포인트 (얇은 레이어)."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from models.response import TrendIndicatorsEnvelope
from modules.stats.schemas import (
    BBMidParams,
    ComboFilterParams,
    TrendIndicatorsParams,
    HybridAnalysisParams,
    HybridBacktestParams,
    HybridLiveModeParams,
)
from modules.stats.service import (
    run_bb_mid_analysis,
    run_combo_filter_analysis,
    run_hybrid_analysis_service,
    run_hybrid_backtest_service,
    run_hybrid_live_service,
    run_trend_indicators_analysis,
)
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["stats"])


# ========== API Endpoints ==========

@router.post("/bb-mid")
@handle_api_errors(include_traceback=False)
async def api_bb_mid(params: BBMidParams):
    """Calculate BB Mid Touch statistics"""
    return await run_in_threadpool(
        run_bb_mid_analysis,
        params.coin,
        params.intervals,
        params.start_side,
        params.max_bars,
        params.regime,
        params.use_csv,
    )


@router.post("/combo-filter")
@handle_api_errors(include_traceback=False)
async def api_combo_filter(params: ComboFilterParams):
    """Run combo filter backtest"""
    return await run_in_threadpool(run_combo_filter_analysis, params.model_dump())


@router.post("/trend-indicators", response_model=TrendIndicatorsEnvelope)
@handle_api_errors(include_traceback=False)
async def api_trend_indicators(params: TrendIndicatorsParams):
    """추세판단 지표 조회 (Slow Stochastic, MACD, ADX, RSI, VWAP, Supertrend)"""
    return await run_in_threadpool(
        run_trend_indicators_analysis,
        params.coin,
        params.interval,
        params.use_csv,
    )


@router.post("/hybrid-analysis")
@handle_api_errors(include_traceback=False)
async def api_hybrid_analysis(params: HybridAnalysisParams):
    """
    하이브리드 전략 분석
    
    여러 지표를 조합한 전략들의 시그널 발생 통계를 분석합니다.
    """
    return await run_in_threadpool(
        run_hybrid_analysis_service,
        params.coin,
        params.interval,
        params.strategies,
    )


@router.post("/hybrid-backtest")
@handle_api_errors(include_traceback=False)
async def api_hybrid_backtest(params: HybridBacktestParams):
    """
    하이브리드 전략 백테스팅
    
    TP/SL 기반의 현실적인 매매 시뮬레이션을 수행합니다.
    """
    return await run_in_threadpool(
        run_hybrid_backtest_service,
        params.coin,
        params.interval,
        params.strategy,
        params.tp,
        params.sl,
        params.max_hold,
    )


@router.post("/hybrid-live")
@handle_api_errors(include_traceback=False)
async def api_hybrid_live(params: HybridLiveModeParams):
    """
    하이브리드 전략 라이브 모드
    
    현재 시점에서 각 전략의 시그널 상태를 확인합니다.
    """
    return await run_in_threadpool(
        run_hybrid_live_service,
        params.coin,
        params.interval,
        params.strategies,
    )
