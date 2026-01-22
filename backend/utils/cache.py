"""
데이터 캐싱 유틸리티 모듈

TTL 기반 영속 캐시를 제공합니다 (diskcache 사용).
서버 재시작 후에도 캐시가 유지됩니다.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from diskcache import Cache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    # Fallback to in-memory cache if diskcache is not available
    from datetime import datetime, timedelta as td


class DataCache:
    """
    TTL 기반 영속 캐시 (diskcache 사용)
    
    서버 재시작 후에도 캐시가 유지되며, 디스크에 저장됩니다.
    
    Attributes:
        ttl_seconds: 캐시 TTL (초 단위)
        _cache: diskcache.Cache 인스턴스
        _hits: 캐시 히트 횟수
        _misses: 캐시 미스 횟수
    """
    
    def __init__(self, ttl_minutes: int = 5, cache_dir: Optional[str] = None):
        """
        Args:
            ttl_minutes: 캐시 TTL (분 단위)
            cache_dir: 캐시 디렉토리 경로 (None이면 기본값 사용)
        """
        self.ttl_seconds = ttl_minutes * 60
        
        if DISKCACHE_AVAILABLE:
            # 캐시 디렉토리 설정
            if cache_dir is None:
                # 프로젝트 루트의 .cache 디렉토리 사용
                project_root = Path(__file__).parent.parent.parent
                cache_dir = str(project_root / ".cache" / "data")
            
            # 디렉토리 생성
            os.makedirs(cache_dir, exist_ok=True)
            
            # diskcache 인스턴스 생성
            self._cache = Cache(cache_dir, size_limit=2**30)  # 1GB 제한
            self._use_diskcache = True
        else:
            # Fallback: 메모리 캐시
            self._cache: Dict[str, Any] = {}
            self._timestamps: Dict[str, datetime] = {}
            self._use_diskcache = False
        
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기
        
        Args:
            key: 캐시 키
        
        Returns:
            캐시된 값 또는 None (미스 또는 만료)
        """
        if self._use_diskcache:
            # diskcache.get()은 기본적으로 TTL을 자동 처리
            # expire_time=False로 하면 값만 반환 (TTL 체크는 내부적으로 처리)
            value = self._cache.get(key, default=None)
            if value is not None:
                self._hits += 1
                return value
            else:
                self._misses += 1
                return None
        else:
            # Fallback: 메모리 캐시
            if key in self._cache:
                if datetime.now() - self._timestamps[key] < timedelta(seconds=self.ttl_seconds):
                    self._hits += 1
                    return self._cache[key]
                else:
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
        if self._use_diskcache:
            # diskcache는 expire 파라미터로 TTL 설정
            self._cache.set(key, value, expire=self.ttl_seconds)
        else:
            # Fallback: 메모리 캐시
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
    
    def clear(self) -> None:
        """캐시 초기화"""
        if self._use_diskcache:
            self._cache.clear()
        else:
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
        
        if self._use_diskcache:
            # diskcache는 len()과 keys()를 지원
            cached_items = len(self._cache)
            # iterkeys()는 Python 2 스타일, Python 3에서는 keys() 사용
            try:
                keys = list(self._cache.iterkeys())[:10]
            except AttributeError:
                keys = list(self._cache.keys())[:10]
        else:
            cached_items = len(self._cache)
            keys = list(self._cache.keys())[:10]
        
        return {
            "cached_items": cached_items,
            "keys": keys[:10],  # 처음 10개만 반환 (너무 많을 수 있음)
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),  # 히트율 (%)
            "persistent": self._use_diskcache,  # 영속 캐시 사용 여부
        }
