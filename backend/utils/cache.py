"""
데이터 캐싱 유틸리티 모듈

TTL 기반 메모리 캐시를 제공합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class DataCache:
    """
    간단한 TTL 기반 메모리 캐시
    
    Attributes:
        ttl: 캐시 TTL (timedelta)
        _cache: 캐시 데이터 딕셔너리
        _timestamps: 캐시 타임스탬프 딕셔너리
        _hits: 캐시 히트 횟수
        _misses: 캐시 미스 횟수
    """
    
    def __init__(self, ttl_minutes: int = 5):
        """
        Args:
            ttl_minutes: 캐시 TTL (분 단위)
        """
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self._hits = 0  # 캐시 히트 횟수
        self._misses = 0  # 캐시 미스 횟수
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기
        
        Args:
            key: 캐시 키
        
        Returns:
            캐시된 값 또는 None (미스 또는 만료)
        """
        if key in self._cache:
            if datetime.now() - self._timestamps[key] < self.ttl:
                self._hits += 1
                return self._cache[key]
            else:
                # TTL 만료
                del self._cache[key]
                del self._timestamps[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self) -> None:
        """캐시 초기화"""
        self._cache.clear()
        self._timestamps.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환 (히트율 포함)
        
        Returns:
            캐시 통계 딕셔너리
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "cached_items": len(self._cache),
            "keys": list(self._cache.keys()),
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2)  # 히트율 (%)
        }
