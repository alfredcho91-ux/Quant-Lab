"""
데이터 및 분석 결과 캐싱 처리
"""
from typing import Dict, Any
import hashlib
import json
from pathlib import Path
from utils.cache import DataCache
from strategy.context import AnalysisContext

# 캐시 디렉토리 설정
project_root = Path(__file__).parent.parent.parent.parent
cache_base = project_root / ".cache"

# 전역 캐시 인스턴스
# 데이터 캐시 (TTL 5분)
data_cache = DataCache(ttl_minutes=5, cache_dir=str(cache_base / "data"))

# 분석 결과 캐시 (TTL 10분)
analysis_cache = DataCache(ttl_minutes=10, cache_dir=str(cache_base / "analysis"))

# 지표 계산 캐시 (TTL 30분)
indicators_cache = DataCache(ttl_minutes=30, cache_dir=str(cache_base / "indicators"))


def generate_analysis_cache_key(context: AnalysisContext) -> str:
    """
    분석 결과 캐시 키 생성
    Format: coin_interval_n_streak_direction[_complex_hash|_rsiXX_bodyYY]_emaZZ
    """
    base_key = f"{context.coin}_{context.interval}_{context.n_streak}_{context.direction}"
    ema_key = f"_ema{context.ema_200_position or 'any'}"
    
    # complex_pattern이 있으면 해시값 포함
    if context.use_complex_pattern and context.complex_pattern:
        pattern_str = json.dumps(context.complex_pattern, sort_keys=True)
        pattern_hash = hashlib.md5(pattern_str.encode()).hexdigest()[:8]
        return f"{base_key}_complex_{pattern_hash}{ema_key}"
    
    # Simple mode: 필터/임계값 변화를 캐시 키에 반영
    rsi_key = f"_rsi{int(context.rsi_threshold)}"
    
    # [Fix] 명시적 float 변환으로 0.0/None 처리 강화
    body_val = float(context.min_total_body_pct or 0)
    
    if body_val <= 0:
        body_key = "_bodynone"
    else:
        # 소수점 1자리까지 포함하여 유니크 키 생성 (예: _body10.0)
        body_key = f"_body{body_val:.1f}"

    return f"{base_key}{rsi_key}{body_key}{ema_key}"


def get_cache_stats() -> Dict[str, Any]:
    """캐시 상태 확인 (데이터 + 분석 + 지표)"""
    data_stats = data_cache.stats()
    analysis_stats = analysis_cache.stats()
    indicators_stats = indicators_cache.stats()

    total_hits = data_stats["hits"] + analysis_stats["hits"] + indicators_stats["hits"]
    total_misses = data_stats["misses"] + analysis_stats["misses"] + indicators_stats["misses"]
    total_requests = total_hits + total_misses

    per_cache_metrics = {
        "data_cache": {
            "hits": data_stats["hits"],
            "misses": data_stats["misses"],
            "requests": data_stats["total_requests"],
            "hit_rate": data_stats["hit_rate"],
            "cached_items": data_stats["cached_items"],
        },
        "analysis_cache": {
            "hits": analysis_stats["hits"],
            "misses": analysis_stats["misses"],
            "requests": analysis_stats["total_requests"],
            "hit_rate": analysis_stats["hit_rate"],
            "cached_items": analysis_stats["cached_items"],
        },
        "indicators_cache": {
            "hits": indicators_stats["hits"],
            "misses": indicators_stats["misses"],
            "requests": indicators_stats["total_requests"],
            "hit_rate": indicators_stats["hit_rate"],
            "cached_items": indicators_stats["cached_items"],
        },
    }

    return {
        "data_cache": data_stats,
        "analysis_cache": analysis_stats,
        "indicators_cache": indicators_stats,
        "per_cache_metrics": per_cache_metrics,
        "total_cached_items": data_stats["cached_items"] + analysis_stats["cached_items"] + indicators_stats["cached_items"],
        "total_hits": total_hits,
        "total_misses": total_misses,
        "total_requests": total_requests,
        "total_hit_rate": round(total_hits / max(total_requests, 1) * 100, 2),
    }


def clear_cache() -> Dict[str, Any]:
    """모든 캐시 초기화"""
    data_cache.clear()
    analysis_cache.clear()
    indicators_cache.clear()
    return {"success": True, "message": "All caches cleared"}
