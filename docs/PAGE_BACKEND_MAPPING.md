# 화면-백엔드 매핑

문서 기준일: 2026-08-17. 이 표는 현재 `frontend/src/App.tsx`의 경로와 `backend/main.py`의 라우터 등록을 기준으로 합니다.

## 주요 화면

| 화면/경로 | 프런트 주요 코드 | API | 백엔드 계산 경로 |
| --- | --- | --- | --- |
| 추세판단 `/trend-judgment` | `pages/TrendJudgmentPage.tsx`, `components/IndicatorProjectionCard.tsx`, `components/VPVRTable.tsx`, `components/MomentumIndicatorPanels.tsx` | `POST /api/trend-indicators`, `GET /api/indicators/projection`, `GET /api/indicators/vpvr/{coin}/{interval}` | `modules/stats/service.py`, `modules/indicators/service.py`, `core/indicators.py`, `core/vpvr.py` |
| 전용 차트 `/trend-chart` | `pages/TrendChartPage.tsx`, `components/TrendPriceChart.tsx` | `GET /api/indicators/projection`, `GET /api/indicators/vpvr/{coin}/{interval}`, `GET /api/ohlcv/{coin}/{interval}` | `modules/indicators/service.py`, `core/vpvr.py` |
| AI Lab `/ai-backtest-lab` | `pages/AIStrategyLabPage.tsx`, `features/ai-lab/` | `POST /api/ai/research`, `POST /api/ai/analyst` | `modules/ai_lab/` |
| 연속봉 분석 `/streak-analysis` | `pages/StreakAnalysisPage.tsx`, `features/streak-analysis/` | `POST /api/streak-analysis`, cache stats/clear | `modules/streak/`, `strategy/streak/` |
| 조합 필터 `/combo-filter` | `pages/ComboFilterPage.tsx` | `POST /api/combo-filter` | `modules/stats/service.py`, `strategy/combo_filter/` |
| 복리 계산기 `/compound-calculator` | `pages/TradingCompoundCalculatorPage.tsx`, `features/compound-calculator/` | 없음 | 브라우저 내 계산 |
| 홀딩/재진입 `/hold-reentry` | `pages/HoldReentryPage.tsx`, `utils/holdReentry.ts` | 없음 | 브라우저 내 계산 |
| 기본 백테스트 `/backtest` | `pages/BacktestPage.tsx` | `POST /api/backtest`, 전략 메타데이터 API, 프리셋 API | `modules/backtest/`, `core/backtest.py`, `core/strategies.py` |
| 매매일지 `/journal` | `pages/JournalPage.tsx` | `GET/POST/DELETE /api/journal`, `GET /api/deepcoin/status`, `GET /api/deepcoin/trade-markers`, `POST /api/deepcoin/sync` | `modules/journal/`, `modules/deepcoin/`, `core/indicator_pipelines.py`, `core/vpvr.py` |
| 매매 분석 `/trade-analysis` | `pages/TradeAnalysisPage.tsx`, `features/tradeAnalysis/CurrentMarketSimilarityPanel.tsx`, `TradeQualityAnalysis.tsx` | `GET /api/journal`, `GET /api/journal/current-market`, `GET /api/journal/quality-analysis`, `GET /api/journal/stop-loss-analysis` | `modules/journal/current_market.py`, `analysis.py`, `quality_analysis.py`, `quality_market.py`, `stop_loss_analysis.py`, `core/indicator_pipelines.py` |

## 직접 경로 유지 화면

`/bb-mid`는 `BBMidPage`와 `POST /api/bb-mid`가 남아 있는 직접 접근 경로입니다. 현재 사이드바에는 노출하지 않으며, 신규 기능의 기준 화면으로 사용하지 않습니다.

## 공통 연결

| 관심사 | 위치 | 역할 |
| --- | --- | --- |
| 공용 선택 상태 | `frontend/src/store/useStore.ts` | 코인, 시간대, 언어, UI 상태 |
| API 진입점 | `frontend/src/api/client.ts` | 기능별 클라이언트 re-export |
| Axios와 오류 | `frontend/src/api/config.ts` | envelope 해제 및 typed error |
| 시장 데이터 | `backend/modules/market/`, `backend/utils/data_service.py` | Binance/CSV OHLCV와 보조 시장 데이터 |
| 캐시 | `backend/utils/cache.py` | diskcache 우선 TTL 캐시 |
| 설정 | `backend/config/settings.py` | 환경 변수와 프로젝트 기준 파일 경로 |

## Deepcoin 동기화 상세

1. `JournalPage`는 Deepcoin API secret을 입력하거나 보관하지 않고, 서버의 설정 여부만 확인합니다.
2. 동기화는 현물 또는 USDT 무기한 체결을 `billId` 기반으로 페이지네이션해 가져옵니다.
3. 새 체결은 `journal_entries.external_id` unique index로 한 번만 저장됩니다.
4. 지표값은 Binance Spot에서 체결 직전 확정봉을 기준으로 1h/2h/4h/1d RSI, MACD, 3 Slow Stochastic, Stoch RSI, VPVR를 계산해 `indicator_snapshot` JSON으로 함께 저장합니다.

## 추세판단 상세

1. 추세판단은 같은 코인·시간대의 추세 지표, VPVR, 가격 투영을 React Query로 소유하고, 전용 차트만 OHLCV를 추가로 요청합니다.
2. `run_trend_indicators_analysis()`는 600봉으로 지표를 계산하고, 마지막 진행봉을 빼고 직전 확정봉을 `latest`로 반환합니다.
3. 차트 데이터는 `getCompletedCandles()`로 최근 200개 확정봉만 사용합니다.
4. `run_indicator_projection_service()`는 RSI 30/70 목표가와 시간대별 anchored/200봉 rolling VWAP을 계산합니다.
5. `run_vpvr_service()`는 Binance quote volume을 24개 가격 bin에 캔들 범위 비례로 배분합니다.
6. 두 화면은 공용 `useHourlyRefresh` 훅으로 정각마다 갱신하고, 가시화 재요청은 마지막 갱신 후 1시간이 지났을 때만 수행합니다.

## 변경 시 확인할 것

- API를 바꾸면 `frontend/src/api/`, `frontend/src/types/`, 해당 `schemas.py`, 이 문서를 함께 갱신합니다.
- 새로운 화면은 `App.tsx` 경로와 필요 시 `Sidebar.tsx` 메뉴를 모두 검토합니다.
- 라우터에서는 서비스만 호출합니다. `python3 scripts/check_route_imports.py`로 경계를 확인합니다.
- `core/`를 바꾸면 `python3 scripts/check_core_imports.py`를 실행합니다.
