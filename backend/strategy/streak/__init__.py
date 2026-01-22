"""
전략 패키지 - 연속봉 분석 (Streak Analysis)

Public API:
- analyze_streak_pattern: 메인 분석 함수
- get_cache_stats: 캐시 상태 조회
- clear_cache: 캐시 초기화
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

from strategy.context import AnalysisContext
from strategy.streak.common import (
    load_data,
    prepare_dataframe,
    get_cache_stats,
    clear_cache,
    generate_analysis_cache_key,
    analysis_cache
)
from strategy.streak.simple_strategy import run_simple_analysis
from strategy.streak.complex_strategy import run_complex_analysis


def analyze_streak_pattern(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    연속봉 패턴 분석 메인 함수 (분석 결과 캐싱 포함)
    
    Args:
        params: 분석 파라미터 딕셔너리
            - coin: 코인 심볼 (예: 'BTC')
            - interval: 타임프레임 (예: '1d', '4h')
            - n_streak: 연속 횟수 (Simple Mode)
            - direction: 'green' 또는 'red' (Simple Mode)
            - use_complex_pattern: Complex Mode 사용 여부
            - complex_pattern: 복합 패턴 배열 (예: [1, 1, 1, -1, -1])
            - rsi_threshold: RSI 임계값
            - max_retracement: 최대 되돌림 비율
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        # 1. Context 생성 및 검증
        context = AnalysisContext.from_params(params)
        validation_error = context.validate()
        if validation_error:
            return validation_error
        
        # 2. 분석 결과 캐시 확인
        cache_key = generate_analysis_cache_key(context)
        cached_result = analysis_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Analysis cache hit: {cache_key}")
            cached_result['from_cache'] = True
            cached_result['analysis_cached'] = True
            return cached_result
        
        # 3. Mode 결정
        mode = context.determine_mode()
        
        # 4. 데이터 로딩
        df, from_cache = load_data(context.coin, context.interval)
        if df is None or df.empty:
            return {"success": False, "error": "Failed to load data"}
        
        # 5. DataFrame 준비
        df = prepare_dataframe(df, context.direction)
        
        # 6. Mode 분기 및 분석 실행
        if mode == "complex":
            result = run_complex_analysis(df, context, from_cache)
        else:
            result = run_simple_analysis(df, context, from_cache)
        
        # 7. 결과에 메타데이터 추가
        result['from_cache'] = from_cache
        result['analysis_cached'] = False
        result['mode'] = mode
        
        # 8. 분석 결과 캐싱
        analysis_cache.set(cache_key, result)
        logger.debug(f"Analysis result cached: {cache_key}")
        
        return result
        
    except Exception as e:
        import traceback
        logger.error(f"Error in analyze_streak_pattern: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc()
        }


__all__ = [
    'analyze_streak_pattern',
    'get_cache_stats',
    'clear_cache'
]
