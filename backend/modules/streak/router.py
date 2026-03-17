"""연속 봉 분석 (Streak Analysis) API"""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from modules.streak.schemas import StreakAnalysisParams
from modules.streak.service import clear_streak_cache, get_streak_cache_stats, run_streak_analysis
from models.response import StreakAnalysisEnvelope
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["streak"])


@router.post("/streak-analysis", response_model=StreakAnalysisEnvelope)
@handle_api_errors(include_traceback=False)
async def api_streak_analysis(params: StreakAnalysisParams):
    """
    연속봉 패턴 분석 (양봉/음봉 연속성 분석)
    
    - Simple Mode: n개 연속 양봉/음봉 이후 지속/반전 확률
    - Complex Mode: 복합 패턴 (예: 3양봉 + 2음봉) 이후 확률
    - C1 분석: 패턴 완성 후 다음 봉(C1)의 지속/반전 확률
    - C2 분석: C1 결과에 따른 C2 예측
    - ATR & Z-Score: 변동성 분석
    """
    return await run_in_threadpool(run_streak_analysis, params.model_dump())


@router.get("/streak-cache-stats")
async def api_get_cache_stats():
    """캐시 상태 확인"""
    return await run_in_threadpool(get_streak_cache_stats)


@router.post("/streak-cache-clear")
async def api_clear_cache():
    """캐시 초기화"""
    return await run_in_threadpool(clear_streak_cache)
