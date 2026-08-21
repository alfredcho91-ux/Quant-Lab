# 계산 코드 맵

주요 수치가 어디서 계산되는지 빠르게 찾기 위한 안내입니다. API의 입출력 계약은 [API_SPEC.md](../API_SPEC.md), 화면 연결은 [PAGE_BACKEND_MAPPING.md](./PAGE_BACKEND_MAPPING.md)를 봅니다.

## 추세판단과 VPVR

| 항목 | 진입점 | 계산 위치 | 기준 |
| --- | --- | --- | --- |
| 추세 지표 | `POST /api/trend-indicators` | `backend/modules/stats/service.py::run_trend_indicators_analysis` | 600봉 로드, 직전 확정봉 결과, 최근 200개 확정봉 시계열 |
| 지표 파이프라인 | 위 서비스 | `core/indicators.py::build_indicator_adapter` | Trend Judgment mode |
| RSI 30/70 목표가 | `GET /api/indicators/projection` | `modules/indicators/reverse_calc.py::calculate_required_price_for_rsi` | Wilder RMA RSI 14, 다음 봉 종가 역산 |
| 현재 RSI와 VWAP | 위 endpoint | `modules/indicators/reverse_calc.py::get_indicator_projections` | 마지막 확정봉 |
| anchored/rolling VWAP 선택 | 위 service | `modules/indicators/service.py::PROJECTION_VWAP_ANCHORS`, `PROJECTION_ROLLING_VWAP_WINDOWS` | 시간대별 day/week/month/quarter/year, 필요 시 200봉 |
| VPVR 입력 | `GET /api/indicators/vpvr/{coin}/{interval}` | `modules/indicators/service.py::_load_vpvr_candles` | 기본 240/180/300봉, 진행봉 제외 |
| VPVR profile | 위 endpoint | `core/vpvr.py::calculate_vpvr` | 24 price bins, 70% Value Area, quote volume |
| VPVR POC/Value Area | `core/vpvr.py` | `_serialize_profile`, `_expand_value_area` | 최대 volume bin과 인접 bin 확장 |

### VPVR 해석 주의

`calculate_vpvr()`은 개별 체결가가 아닌 kline의 `quote_volume`을 사용합니다. 각 캔들의 고가-저가와 가격 bin의 겹침 길이에 비례해 거래량을 배분하므로 `allocation_method=candle_range_proportional`입니다. 실제 거래소의 tick-by-price profile과 동일한 계산이 아닙니다.

## Deepcoin 체결 시점 스냅샷

| 항목 | 진입점 | 계산 위치 | 기준 |
| --- | --- | --- | --- |
| 체결 동기화 | `POST /api/deepcoin/sync` | `modules/deepcoin/service.py::sync_deepcoin_fills_service` | Deepcoin read-only fills, `billId` 중복 방지 |
| API 서명 | 위 service | `DeepcoinClient.build_headers` | `timestamp + method + requestPath + body` HMAC-SHA256/Base64 |
| 확정봉 선택 | 위 service | `_indicator_snapshot_for_fill` | Deepcoin 체결시각보다 이전에 종료된 마지막 Binance Spot candle |
| RSI, MACD, Stoch | 위 service | `core/indicator_pipelines.py::compute_trend_judgment_indicators` | 1h/2h/4h/1d, 기존 추세판단 수식 재사용 |
| VPVR | 위 service | `core/vpvr.py::calculate_vpvr` | 24 bins, 240봉(일봉 180봉), Binance quote volume |

저널의 `indicator_snapshot`에는 계산 결과와 `market_source=binance_spot_klines`를 함께 저장합니다. Deepcoin 체결 가격과 Binance Spot 지표 기준 가격은 일치하지 않을 수 있습니다.

## 연속봉 확률 분석

| 항목 | 위치 | 책임 |
| --- | --- | --- |
| API 진입 | `backend/modules/streak/router.py` | Pydantic 요청 검증과 서비스 호출 |
| 서비스 진입 | `backend/modules/streak/service.py` | 요청 payload 정리 |
| 분석 분기 | `backend/strategy/streak/__init__.py::analyze_streak_pattern` | `AnalysisContext`, cache, Simple/Complex 선택 |
| Simple 분석 | `strategy/streak/simple_strategy.py::run_simple_analysis` | N연속 봉, C1/C2 결과 |
| Complex 분석 | `strategy/streak/complex_strategy.py::run_complex_analysis` | 사용자 패턴, pullback, 보조 통계 |
| 공통 분석 | `strategy/streak/common.py` | DataFrame 준비, interval 통계, score |
| 통계 | `strategy/streak/statistics.py` | Wilson confidence interval 등 |
| 캐시 | `strategy/streak/cache_ops.py` | data, analysis, indicator cache |

핵심 불변식: `C1`은 패턴 완성 봉이 아닌 `T+1`, `C2`는 `T+2`입니다. Heikin-Ashi를 선택해도 패턴 해석에만 쓰며 RSI, ATR, Disparity, EMA 200은 원본 OHLC를 기준으로 유지합니다.

## 그 외 전략 계산

| 기능 | API | 주요 코드 |
| --- | --- | --- |
| BB Mid | `POST /api/bb-mid` | `strategy/bb_mid/logic.py` |
| 조합 필터 | `POST /api/combo-filter` | `strategy/combo_filter/logic.py` |
| 하이브리드 | `POST /api/hybrid-*` | `strategy/hybrid/logic.py`, `strategy/hybrid/backtest.py` |
| 기본 백테스트 | `POST /api/backtest` | `modules/backtest/service.py`, `core/backtest.py`, `core/strategies.py` |
| 지지·저항 | `GET /api/support-resistance/{coin}/{interval}` | `modules/support_resistance/service.py`, `core/support_resistance.py` |
| 복리 계산기 | 브라우저 내 | `frontend/src/features/compound-calculator/calculations.ts` |

## 변경 전 확인

1. 지표 수식 변경은 `core/` 단위 테스트와 기존 전략별 기대값에 영향을 줄 수 있습니다.
2. API response field를 바꾸면 해당 Pydantic schema, `frontend/src/api/`, `frontend/src/types/`, 화면을 함께 수정합니다.
3. 확정봉 기준을 바꾸지 않습니다. 진행봉을 포함해야 하는 별도 기능이라면 response field와 UI에 기준을 명시합니다.
4. VPVR의 bin 수, Value Area, 가격 범위 변경은 화면 설명과 [README.md](../README.md)를 함께 갱신합니다.
