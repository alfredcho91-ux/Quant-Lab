"""연속 봉 분석 (Streak Analysis) API"""

from fastapi import APIRouter
from models.request import StreakAnalysisParams
from utils.decorators import handle_api_errors
from strategy import (
    analyze_streak_pattern,
    get_cache_stats,
    clear_cache,
)

router = APIRouter(prefix="/api", tags=["streak"])


@router.post("/streak-analysis")
@handle_api_errors(include_traceback=True)
async def api_streak_analysis(params: StreakAnalysisParams):
    """
    연속봉 패턴 분석 (양봉/음봉 연속성 분석)
    
    - Simple Mode: n개 연속 양봉/음봉 이후 지속/반전 확률
    - Complex Mode: 복합 패턴 (예: 3양봉 + 2음봉) 이후 확률
    - C1 분석: 패턴 완성 후 다음 봉(C1)의 지속/반전 확률
    - C2 분석: C1 결과에 따른 C2 예측
    - ATR & Z-Score: 변동성 분석
    """
    params_dict = params.model_dump()
    return analyze_streak_pattern(params_dict)


@router.get("/streak-cache-stats")
async def api_get_cache_stats():
    """캐시 상태 확인"""
    return get_cache_stats()


@router.post("/streak-cache-clear")
async def api_clear_cache():
    """캐시 초기화"""
    return clear_cache()
