# 캐시 정책

문서 기준일: 2026-08-03. 캐시는 응답을 오래 보관하기 위한 기능이 아니라, 같은 분석 화면이 짧은 시간에 같은 데이터를 반복 요청하지 않도록 하는 장치입니다.

## 공통 구현

모든 서버 캐시는 `backend/utils/cache.py::DataCache`를 사용합니다.

- 기본 backend: `diskcache`
- fallback: 프로세스 메모리
- 비활성화/메모리 강제: `DATA_CACHE_BACKEND=memory`, `off`, `disabled`, `none`
- 메모리 fallback 상한: `MEMORY_CACHE_MAX_ITEMS`, 기본 5000
- 기본 디스크 위치: `<project>/.cache/data` 또는 호출자가 지정한 하위 경로

## 현재 TTL

| 영역 | 코드 위치 | TTL | 목적 |
| --- | --- | ---: | --- |
| CSV 시간대 탐색 | `data_service.py::discover_timeframes` | 5초 | 파일 목록 반복 스캔 방지 |
| Fear & Greed | `data_service.py::get_fear_and_greed_index` | 300초 | 외부 API 재사용 |
| BTC/ETH/SOL ticker | `data_service.py::get_market_prices` | 30초 | 사이드바 가격 갱신 |
| Binance kline | `data_service.py::fetch_binance_klines` | 30초 | 같은 symbol·timeframe·봉 수 요청 재사용 |
| 연속봉 DataFrame | `strategy/streak/cache_ops.py::data_cache` | 5분 | 분석 원천 DataFrame 재사용 |
| 연속봉 분석 결과 | `strategy/streak/cache_ops.py::analysis_cache` | 10분 | 동일 조건 분석 재사용 |
| 연속봉 지표 | `strategy/streak/cache_ops.py::indicators_cache` | 30분 | 지표 계산 재사용 |
| 추세판단 React Query | `TrendJudgmentPage.tsx` | 60분 stale, 65분 GC | 지표·VPVR·투영·차트의 중복 화면 요청 방지 |

## 추세판단 동작

- 서버의 kline 캐시는 API 응답부터 30초 동안 재사용합니다.
- 프런트는 같은 쿼리를 1시간 동안 stale로 취급하고 재연결 refetch를 하지 않습니다.
- 자동 갱신은 다음 정각에 맞추며, 탭이 다시 보일 때는 마지막 갱신 이후 1시간이 지난 경우에만 다시 요청합니다.
- 수동 새로고침은 활성 추세 지표, VPVR, OHLCV 차트, 가격 투영 쿼리를 함께 갱신합니다.

이 조합은 화면을 다시 오갈 때 불필요한 Binance 요청을 줄이면서, 시간봉 기준 분석값은 정기적으로 최신 확정봉에 맞추는 목적입니다.

## 운영 규칙

1. 새 캐시는 `DataCache` 외 별도 구현을 만들지 않습니다.
2. 캐시 키는 정규화된 입력값과 계산에 영향을 주는 파라미터를 모두 포함해야 합니다.
3. 진행 중 봉과 확정봉을 섞지 않습니다. 추세판단 응답과 VPVR/투영 서비스는 마지막 진행봉을 제외합니다.
4. TTL을 바꾸면 코드, 이 문서, 해당 화면의 갱신 정책을 같은 변경에서 맞춥니다.
5. 가격·체결 데이터는 캐시 결과를 실시간 시세로 오해하지 않도록 UI와 문서에 기준을 표시합니다.
