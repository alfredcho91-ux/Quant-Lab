# 프로젝트 파일 구조

## 📁 전체 구조

```
my_quant_V2/
├── backend/              # FastAPI 백엔드
├── frontend/            # React + TypeScript 프론트엔드
├── core/                # 공통 코어 로직 (레거시)
└── binance_klines/      # CSV 데이터 저장소
```

---

## 🔧 Backend 구조

### 주요 파일
- `main.py` - FastAPI 앱 진입점
- `__init__.py` - 프로젝트 루트 경로 설정 (sys.path 통합 관리)

### 📂 backend/routes/
API 엔드포인트 라우터들:
- `backtest.py` - 백테스트 API
- `journal.py` - 매매 일지 API
- `market.py` - 시장 데이터 API
- `stats.py` - 통계 분석 API (MA Cross, BB Mid, Combo Filter, Multi-TF Squeeze, Weekly Pattern)
- `streak.py` - 연속 봉 분석 API
- `scanner.py` - 스캐너 API
- `strategies.py` - 전략 정보 API
- `strategy.py` - 전략 실행 API
- `preset.py` - 프리셋 API
- `support_resistance.py` - 지지/저항선 API

### 📂 backend/strategy/
전략별 로직 모듈:

#### `streak/` - 연속 봉 패턴 분석
- `common.py` - 공통 함수 (데이터 준비, 통계 계산)
- `simple_strategy.py` - 단순 패턴 분석
- `complex_strategy.py` - 복합 패턴 분석
- `statistics.py` - 통계 계산 함수

#### `weekly_pattern/` - 주간 패턴 분석
- `logic.py` - 메인 분석 로직
- `data_processing.py` - 데이터 준비 및 주간 패턴 추출
- `indicators.py` - 기술적 지표 계산 (RSI, NATR, rel_vol)
- `statistics.py` - 통계 계산
- `config.py` - 설정 클래스 (FilterConfig, AnalysisConfig)
- `validation.py` - 데이터 검증 및 예외 처리
- `backtest.py` - 백테스트 로직

#### `combo_filter/` - 통합 필터 테스트
- `logic.py` - 필터 조합 및 TP 달성률 분석

#### `bb_mid/` - 볼린저 밴드 중단 터치
- `logic.py` - 볼밴 중단 터치 분석

#### `ma_cross/` - 이동평균 교차
- `logic.py` - MA 크로스 통계

#### `squeeze/` - 멀티 타임프레임 스퀴즈
- `logic.py` - 스퀴즈 분석

#### 공통 파일
- `common.py` - 공통 통계 함수 (Sharpe Ratio, MDD, Profit Factor 등)
- `context.py` - AnalysisContext (분석 컨텍스트 데이터클래스)

### 📂 backend/utils/
유틸리티 모듈:
- `data_service.py` - 데이터 소스 접근 (Binance API, CSV 로딩)
- `data_loader.py` - 공통 데이터 로딩 함수 (CSV 우선, API 폴백)
- `cache.py` - DataCache 클래스 (TTL 기반 메모리 캐시)
- `decorators.py` - API 에러 처리 데코레이터
- `error_handler.py` - 에러 핸들러
- `exceptions.py` - 커스텀 예외 클래스
- `response_builder.py` - 응답 빌더
- `validators.py` - 데이터 검증 함수

### 📂 backend/models/
- `request.py` - Pydantic 요청 모델 (StreakAnalysisParams, WeeklyPatternParams 등)

### 📂 backend/services/
서비스 레이어:
- `statistics.py` - 백테스트 통계 계산 (Sharpe Ratio, Sortino Ratio, MDD, Monte Carlo)
- `pattern_logic.py` - 패턴 감지 및 통계 계산

### 📂 backend/config/
설정 파일:
- `settings.py` - 앱 설정
- `strategies.yaml` - 전략 메타데이터
- `patterns.json` - 패턴 정의

---

## 🎨 Frontend 구조

### 📂 frontend/src/

#### `api/` - API 클라이언트 (기능별 분리)
- `client.ts` - 메인 export (모든 API 함수 re-export)
- `config.ts` - axios 인스턴스 및 ApiResponse 타입
- `market.ts` - 시장 데이터 API
- `strategy.ts` - 전략 API
- `backtest.ts` - 백테스트 API
- `stats.ts` - 통계 분석 API (MA Cross, BB Mid, Combo Filter, Multi-TF Squeeze)
- `streak.ts` - 연속 봉 분석 API
- `weekly-pattern.ts` - 주간 패턴 분석 API
- `scanner.ts` - 스캐너 API
- `journal.ts` - 매매 일지 API

#### `pages/` - 페이지 컴포넌트
- `StreakAnalysisPage.tsx` - 연속 봉 분석 페이지
- `WeeklyPatternPage.tsx` - 주간 패턴 분석 페이지
- `ComboFilterPage.tsx` - 통합 필터 테스트 페이지
- `MaCrossPage.tsx` - MA 크로스 통계 페이지
- `BBMidPage.tsx` - 볼밴 중단 터치 페이지
- `MultiTFSqueezePage.tsx` - 멀티 TF 스퀴즈 페이지
- `BacktestPage.tsx` - 백테스트 페이지
- `AdvancedBacktestPage.tsx` - 고급 백테스트 페이지
- `PatternPage.tsx` - 패턴/캔들 통계 페이지
- `PatternScannerPage.tsx` - 패턴 스캐너 페이지
- `StrategyScannerPage.tsx` - 전략 스캐너 페이지
- `ScannerPage.tsx` - 스캐너 페이지
- `JournalPage.tsx` - 매매 일지 페이지

#### `components/` - 공통 컴포넌트
- `Layout.tsx` - 레이아웃
- `Sidebar.tsx` - 사이드바 네비게이션
- `Chart.tsx` - 차트 컴포넌트
- `MetricCard.tsx` - 메트릭 카드
- `ParamsPanel.tsx` - 파라미터 패널
- `TradesTable.tsx` - 거래 테이블
- `Skeleton.tsx` - 로딩 스켈레톤
- `StrategyExplainer.tsx` - 전략 설명
- `DataSourceToggle.tsx` - 데이터 소스 토글

#### `components/weekly-pattern/` - 주간 패턴 전용 컴포넌트
- `PriceInputPanel.tsx` - 가격 입력 패널
- `AnalysisSummary.tsx` - 분석 요약
- `FilterResults.tsx` - 필터 결과
- `BacktestResults.tsx` - 백테스트 결과

#### `features/streak-analysis/` - 연속 봉 분석 기능 모듈
- `components/` - 분석 관련 컴포넌트
  - `AnalysisControls.tsx` - 분석 컨트롤
  - `StatisticsSummary.tsx` - 통계 요약
  - `VolatilityDataGrid.tsx` - 변동성 데이터 그리드
  - `IntervalAnalysisTable.tsx` - 타임프레임별 분석 테이블
  - `NYTradingGuideView.tsx` - NY 거래 가이드
- `hooks/` - 커스텀 훅
  - `useStreakAnalysisForm.ts` - 분석 폼 상태 관리
- `utils/` - 유틸리티
  - `patternHelper.ts` - 패턴 생성 헬퍼

#### `hooks/` - 공통 훅
- `usePageCommon.ts` - 페이지 공통 로직 (언어, 타임프레임 등)
- `useAnalysisMutation.ts` - 분석 API 호출 훅

#### `store/` - 상태 관리
- `useStore.ts` - Zustand 스토어 (선택된 코인, 백테스트 파라미터 등)
- `labels.ts` - 라벨 텍스트

#### `types/` - TypeScript 타입 정의 (기능별 분리)
- `index.ts` - 메인 export (모든 타입 re-export)
- `common.ts` - 공통 타입
- `market.ts` - 시장 데이터 타입
- `backtest.ts` - 백테스트 타입
- `strategy.ts` - 전략 타입
- `stats.ts` - 통계 분석 타입
- `streak.ts` - 연속 봉 분석 타입
- `weekly-pattern.ts` - 주간 패턴 분석 타입
- `journal.ts` - 매매 일지 타입

---

## 📚 주요 문서

- `README.md` - 프로젝트 개요
- `ARCHITECTURE.md` - 아키텍처 문서
- `API.md` - API 문서
- `INSTALL.md` - 설치 가이드
- `OPTIMIZATION_SUMMARY.md` - 최적화 요약
- `STREAK_ANALYSIS_FLOW.md` - 연속 봉 분석 플로우
- `COMPLEX_MODE_FLOW.md` - 복합 모드 플로우
- `CALCULATION_CODE_MAP.md` - 계산 코드 맵

---

## 🔑 주요 아키텍처 특징

### Backend
- **FastAPI** 기반 RESTful API
- **모듈화된 전략 구조**: 각 전략이 독립적인 모듈로 분리
- **공통 유틸리티**: 캐싱, 데이터 로딩, 에러 처리 등
- **타입 안정성**: Pydantic 모델로 요청/응답 검증

### Frontend
- **React + TypeScript** + **Vite**
- **기능별 모듈 분리**: API, 타입, 컴포넌트가 기능별로 분리
- **상태 관리**: Zustand
- **API 호출**: React Query (TanStack Query)
- **스타일링**: Tailwind CSS

### 데이터 흐름
1. 프론트엔드 → API 클라이언트 → 백엔드 라우터
2. 백엔드 라우터 → 전략 모듈 → 데이터 처리
3. 결과 반환 → 프론트엔드 표시

---

## 🚀 실행 방법

### Backend
```bash
cd backend
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

---

## 📝 최근 주요 변경사항

### 2026-01-21: 프로젝트 구조 개선
1. **의존성 관리 개선**
   - `backend/__init__.py` 생성: 프로젝트 루트 경로를 한 곳에서 관리
   - 모든 파일에서 개별 `sys.path.insert` 제거 (19개 파일)
   - 테스트 환경 안정성 향상

2. **데이터 서비스 구조 개선**
   - `data_service.py` → `utils/data_service.py`로 이동
   - 의존성 역전 문제 해결 (utils → data_service)
   - 모든 import 경로 업데이트 (7개 파일)

3. **중복 코드 제거**
   - `services/squeeze_service.py` 삭제 (195줄)
   - `strategy/squeeze/logic.py`를 단일 소스로 사용

4. **명명 개선**
   - `services/backtest_logic.py` → `services/statistics.py` 리네임
   - 파일 역할이 더 명확해짐 (통계 계산 모듈)

### 이전 변경사항
1. **주간 패턴 분석 리팩토링**
   - `logic.py` → `data_processing.py`, `indicators.py`, `statistics.py`, `config.py`, `validation.py`로 분리
   - `rel_vol` 계산 추가 (indicators.py)

2. **통합 필터 테스트 수정**
   - `useAnalysisMutation` 제거 → `useMutation` 직접 사용
   - 결과 표시 조건 개선

3. **타입 및 API 클라이언트 모듈화**
   - 타입을 기능별 파일로 분리
   - API 클라이언트를 기능별 파일로 분리

4. **캐싱 및 컨텍스트 관리**
   - `utils/cache.py` - DataCache 클래스
   - `strategy/context.py` - AnalysisContext 데이터클래스
