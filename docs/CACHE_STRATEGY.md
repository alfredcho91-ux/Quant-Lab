# 캐시 전략 (Cache Strategy)

## 목적

캐시 사용 위치와 TTL을 명확히 정의해 운영/성능 일관성을 확보합니다.

## 공통 인터페이스

모든 캐시는 `backend/utils/cache.py::DataCache`를 사용합니다.

- TTL: `ttl_seconds` 또는 `ttl_minutes`
- 저장소:
  - `diskcache` 사용 가능 시 디스크 영속 캐시
  - 미설치 시 메모리 fallback

## 현재 캐시 맵

| 영역 | 위치 | TTL | 용도 |
|---|---|---:|---|
| 시장 메타 | `backend/utils/data_service.py::discover_timeframes` | 5초 | CSV 타임프레임 탐색 |
| 공포탐욕지수 | `backend/utils/data_service.py::get_fear_and_greed_index` | 300초 | 외부 API 결과 재사용 |
| 시세 티커 | `backend/utils/data_service.py::get_market_prices` | 30초 | 대시보드 시세 조회 |
| Streak 데이터 | `backend/strategy/streak/cache_ops.py::data_cache` | 5분 | 데이터프레임 캐시 |
| Streak 분석 | `backend/strategy/streak/cache_ops.py::analysis_cache` | 10분 | 분석 결과 캐시 |
| Streak 지표 | `backend/strategy/streak/cache_ops.py::indicators_cache` | 30분 | 지표 계산 캐시 |

## 운영 규칙

1. 새 캐시 도입 시 `DataCache` 외 별도 캐시 구현 금지
2. 캐시 키는 요청 파라미터 기반으로 결정적(deterministic) 생성
3. 엔드포인트별 캐시 적용 여부는 서비스 레이어에서 명시
4. TTL 변경 시 이 문서와 코드 주석을 함께 갱신
