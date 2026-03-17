# 페이지별 백엔드 매핑

현재 코드 기준으로 각 페이지가 호출하는 백엔드 라우터/서비스/핵심 계산 모듈을 정리한 문서입니다.  
문서 기준일: 2026-02-27

## 1) 연속 봉 분석 (`StreakAnalysisPage`)

- API: `POST /api/streak-analysis`
- Router: `backend/modules/streak/router.py`
- Service: `backend/modules/streak/service.py`
- Core logic:
  - `backend/strategy/streak/simple_strategy.py`
  - `backend/strategy/streak/complex_strategy.py`
  - `backend/strategy/streak/common.py`
  - `backend/strategy/streak/statistics.py`
  - `backend/strategy/context.py`
- Shared utils:
  - `backend/utils/data_loader.py`
  - `backend/utils/data_service.py`
  - `backend/utils/cache.py`

## 2) 추세판단 (`TrendJudgmentPage`)

- API: `POST /api/trend-indicators`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Core logic:
  - `core/indicators.py` (`compute_trend_judgment_indicators`)
- Shared utils:
  - `backend/utils/data_loader.py`
  - `backend/utils/data_service.py`

## 3) 볼밴 중단 통계 (`BBMidPage`)

- API: `POST /api/bb-mid`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/bb_mid/logic.py`

## 4) 콤보 필터 (`ComboFilterPage`)

- API: `POST /api/combo-filter`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/combo_filter/logic.py`

## 5) 하이브리드 분석 (`HybridAnalysisPage`)

- API:
  - `POST /api/hybrid-analysis`
  - `POST /api/hybrid-backtest`
  - `POST /api/hybrid-live`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/hybrid/logic.py`

## 6) 패턴 통계 (`PatternPage`)

- API: `GET /api/ohlcv/{coin}/{interval}`
- Router: `backend/modules/market/router.py`
- Service: `backend/modules/market/service.py`
- Note: 패턴 분류 자체는 프론트엔드 계산 중심

## 7) 패턴 스캐너 (`PatternScannerPage`)

- API: `POST /api/pattern-scanner`
- Router: `backend/modules/scanner/router.py`
- Service: `backend/modules/scanner/service.py`
- Shared logic:
  - `backend/services/pattern_logic.py`

## 8) 전략 스캐너 (`StrategyScannerPage`)

- API: `POST /api/scanner`
- Router: `backend/modules/scanner/router.py`
- Service: `backend/modules/scanner/service.py`
- Core logic:
  - `core/strategies.py`
  - `core/indicators.py`

## 9) 매매 일지 (`JournalPage`)

- API:
  - `GET /api/journal`
  - `POST /api/journal`
  - `DELETE /api/journal/{entry_id}`
- Router: `backend/modules/journal/router.py`
- Service: `backend/modules/journal/service.py`

## 10) AI 백테스트 랩 (`AIBacktestLabPage`, `AIStrategyLabPage`)

- API: `POST /api/ai/research`
- Router: `backend/modules/ai_lab/router.py`
- Service: `backend/modules/ai_lab/service.py`
- Supporting modules:
  - `backend/modules/ai_lab/prompts.py`
  - `backend/services/ai_clients.py`
  - `backend/modules/backtest/service.py` (백테스트 실행)

## 공통 참고

- Active Router 등록 위치: `backend/main.py`
- 요청 스키마 정식 위치: `backend/modules/*/schemas.py`
- 호환 re-export: `backend/models/request.py`
- 라우터 계층 검증: `scripts/check_route_imports.py`
- 코어 계층 검증: `scripts/check_core_imports.py`
