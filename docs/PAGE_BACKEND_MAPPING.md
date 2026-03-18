# Page-to-Backend Mapping

This document maps each major frontend page to the backend router, service layer, and primary calculation modules it depends on.

Document date: 2026-02-27

## 1. Streak Analysis (`StreakAnalysisPage`)

- API: `POST /api/streak-analysis`
- Router: `backend/modules/streak/router.py`
- Service: `backend/modules/streak/service.py`
- Core logic:
  - `backend/strategy/streak/simple_strategy.py`
  - `backend/strategy/streak/complex_strategy.py`
  - `backend/strategy/streak/common.py`
  - `backend/strategy/streak/statistics.py`
  - `backend/strategy/context.py`
- Shared utilities:
  - `backend/utils/data_loader.py`
  - `backend/utils/data_service.py`
  - `backend/utils/cache.py`

## 2. Trend Judgment (`TrendJudgmentPage`)

- API: `POST /api/trend-indicators`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Core logic:
  - `core/indicators.py` via `compute_trend_judgment_indicators`
- Shared utilities:
  - `backend/utils/data_loader.py`
  - `backend/utils/data_service.py`

## 3. BB Mid Statistics (`BBMidPage`)

- API: `POST /api/bb-mid`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/bb_mid/logic.py`

## 4. Combo Filter (`ComboFilterPage`)

- API: `POST /api/combo-filter`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/combo_filter/logic.py`

## 5. Hybrid Analysis (`HybridAnalysisPage`)

- API:
  - `POST /api/hybrid-analysis`
  - `POST /api/hybrid-backtest`
  - `POST /api/hybrid-live`
- Router: `backend/modules/stats/router.py`
- Service: `backend/modules/stats/service.py`
- Strategy logic:
  - `backend/strategy/hybrid/logic.py`

## 6. Pattern Statistics (`PatternPage`)

- API: `GET /api/ohlcv/{coin}/{interval}`
- Router: `backend/modules/market/router.py`
- Service: `backend/modules/market/service.py`
- Note: candle/pattern classification on this page is primarily frontend-side logic.

## 7. Pattern Scanner (`PatternScannerPage`)

- API: `POST /api/pattern-scanner`
- Router: `backend/modules/scanner/router.py`
- Service: `backend/modules/scanner/service.py`
- Shared logic:
  - `backend/services/pattern_logic.py`

## 8. Strategy Scanner (`StrategyScannerPage`)

- API: `POST /api/scanner`
- Router: `backend/modules/scanner/router.py`
- Service: `backend/modules/scanner/service.py`
- Core logic:
  - `core/strategies.py`
  - `core/indicators.py`

## 9. Journal (`JournalPage`)

- API:
  - `GET /api/journal`
  - `POST /api/journal`
  - `DELETE /api/journal/{entry_id}`
- Router: `backend/modules/journal/router.py`
- Service: `backend/modules/journal/service.py`

## 10. AI Backtest Lab (`AIBacktestLabPage`, `AIStrategyLabPage`)

- API: `POST /api/ai/research`
- Router: `backend/modules/ai_lab/router.py`
- Service: `backend/modules/ai_lab/service.py`
- Supporting modules:
  - `backend/modules/ai_lab/prompts.py`
  - `backend/services/ai_clients.py`
  - `backend/modules/backtest/service.py` for backtest execution

## Shared References

- Active router registration: `backend/main.py`
- Canonical request schemas: `backend/modules/*/schemas.py`
- Compatibility re-export: `backend/models/request.py`
- Router layer guard: `scripts/check_route_imports.py`
- Core layer guard: `scripts/check_core_imports.py`
