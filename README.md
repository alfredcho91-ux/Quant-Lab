# 💎 월젬의 퀀트 마스터 (WolGem's Quant Master)

암호화폐 트레이딩을 위한 종합 분석 및 백테스트 플랫폼입니다.

![License](https://img.shields.io/badge/license-MIT-green)
![React](https://img.shields.io/badge/React-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)

---

## ⚠️ 핵심 제약 조건 (AI 리팩토링 필수 확인사항)

> **🚨 최우선 읽기 필수**: AI가 코드를 수정하기 전에 반드시 이 섹션을 먼저 읽어야 합니다.  
> 아래 규칙들은 통계적 정확성 및 비즈니스 로직의 핵심이므로, 리팩토링이나 최적화 시 절대 변경하지 마세요.

### 🔴 절대 변경 금지 사항

#### 0. 데이터 일관성 보장 (DatetimeIndex 정규화) ⚡ 시스템 로직 최상단

> **🚨 선택이 아닌 필수**: 모든 분석 모듈이 DatetimeIndex를 공유하도록 강제하는 제약 조건입니다.

- **필수 강제 규칙**: 모든 분석용 DataFrame은 반드시 `DatetimeIndex`를 보유해야 함
- **위치**: `backend/strategy/common.py` - `normalize_indices()`
- **시스템 로직 순서**: 데이터 로드 → DatetimeIndex 정규화 → 분석 수행
- **금지 사항**: 
  - 인덱스 타입 검증 로직 생략 금지
  - 다른 인덱스 타입(Int64Index, RangeIndex 등) 허용 금지
  - 정규화 단계 건너뛰기 금지
- **이유**: 
  - 인덱스 기반 접근 시 타입 불일치로 인한 버그 방지
  - 모든 모듈 간 데이터 일관성 보장 (Strong Consistency)
  - 시간대 변환 및 시간 기반 필터링의 정확성 보장
- **구현 예시**:
  ```python
  # ❌ 절대 금지: DatetimeIndex 정규화 없이 분석
  df = pd.read_csv('data.csv')  # 인덱스 타입 불명확
  
  # ✅ 필수: DatetimeIndex 정규화 후 분석
  df = pd.read_csv('data.csv')
  df = normalize_indices(df)  # 반드시 실행
  # 이제 df.index는 DatetimeIndex 타입이 보장됨
  ```

#### 1. 인덱스 처리 규칙: C1 날짜 추출
- **패턴 완성 시점 ≠ 분석 대상**: 패턴 완성 시점(`target_cases.index`, `matched_patterns.index`)이 아닌 **다음 봉(C1, 진입일)**을 분석해야 함
- **위치**: 
  - `backend/strategy/simple_strategy.py` (236-246줄)
  - `backend/strategy/complex_strategy.py` (380-389줄)
- **로직**: 
  ```python
  # ❌ 절대 금지: 패턴 완성 시점 분석
  pattern_dates = target_cases.index  # 잘못된 방식
  
  # ✅ 올바른 방식: 다음 봉(C1) 분석
  for idx in matched_patterns.index:
      pos = df.index.get_loc(idx)
      if pos + 1 < len(df):
          c1_idx = df.index[pos + 1]  # C1 날짜
  ```
- **이유**: 시간대별 분석은 C1(진입일)을 기준으로 해야 통계적으로 의미가 있음

#### 2. `valid_date_count` 로직 (시간대별 분석)
- **위치**: `backend/strategy/common.py` - `calculate_intraday_distribution()`
- **규칙**: 저점과 고점이 **다른** EST 구간에 있는 날짜만 확률 계산에 포함
- **금지**: 
  - 전체 날짜 수 사용 금지
  - 같은 구간에 저점/고점이 모두 있는 날을 확률 계산에 포함 금지
- **이유**: 같은 구간에 저점/고점이 모두 있으면 확률 계산이 왜곡됨

> **참고**: DatetimeIndex 정규화는 위의 [0번 항목](#0-데이터-일관성-보장-datetimeindex-정규화--시스템-로직-최상단)에서 상세 설명되어 있습니다.

### 📐 핵심 통계 공식 (절대 변경 금지)

#### Wilson Score Interval (95% 신뢰구간)
- **공식**: $z = 1.96$ (95% 신뢰수준) 기준, 성공 확률 $p$의 상하한 산출
- **위치**: `backend/strategy/common.py` - `wilson_confidence_interval()`
- **제약**: 샘플 수(N) < 10일 경우 'Low Reliability'로 표시
- **금지**: 공식 변경, $z = 1.96$ 변경, 'Low Reliability' 로직 제거 금지

#### Bonferroni 보정
- **공식**: $\alpha_{adjusted} = \frac{\alpha}{n_{comparisons}}$
  - $\alpha = 0.05$ (원래 유의수준)
  - $n_{comparisons}$: 비교 횟수 (RSI 8구간 = 8)
- **위치**: `backend/strategy/common.py` - `analyze_interval_statistics()`
- **금지**: 보정 로직 제거 금지, 보정 없이 $\alpha = 0.05$만 사용 금지
- **이유**: 다중 비교 시 False Positive 방지 필수

### 🕐 EST 시간대 변환 (절대 변경 금지)
- **위치**: `backend/strategy/common.py` - `calculate_intraday_distribution()`
- **규칙**: UTC → EST/EDT 변환 (✅ **pytz 자동 처리**, DST 자동 전환)
- **구현**: `pytz.timezone('America/New_York')` 사용하여 일광절약시간(DST) 자동 처리
- **구간**: EST/EDT 기준 6개 구간(4시간씩): `[00:00-04:00, 04:00-08:00, ..., 20:00-24:00]`
- **금지**: UTC → EST 변환 로직 제거/변경 금지, 4시간 구간 인덱스 계산 변경 금지, pytz 사용 제거 금지
- **이유**: 뉴욕 거래 시간대 정확한 매핑 필수, DST 자동 처리로 운영 리스크 제거

### 📋 리팩토링 전 체크리스트

코드를 수정하기 전에 반드시 확인하세요:

- [ ] **DatetimeIndex 정규화 (시스템 로직 최상단)**: 모든 DataFrame이 로드 시점에 DatetimeIndex로 정규화되었는가? (선택이 아닌 필수)
- [x] **C1 날짜 추출**: 패턴 완성 시점이 아닌 "다음 봉(C1)"을 분석하는가? (✅ 버그 수정 완료, 2025-01-17)
- [x] **C1 분석 일관성**: continuation/reversal 계산이 C1(T+1) 기준으로 이루어지는가? (✅ 버그 수정 완료, 2025-01-17)
- [x] **C1 검증 유닛 테스트**: C1 날짜가 항상 T+1(패턴 완성 시점의 다음 날짜)임을 증명하는 유닛 테스트가 통과하는가? (✅ 완료, 2025-01-12)
- [ ] **`valid_date_count`**: 저점과 고점이 다른 EST 구간에 있는 날만 확률 계산에 포함하는가?
- [ ] **Wilson Score**: 공식이 변경되지 않았는가? $z = 1.96$ 유지하는가?
- [ ] **Bonferroni 보정**: 다중 비교 보정이 적용되는가?
- [x] **EST 변환**: UTC → EST/EDT 시간대 변환이 정확한가? (✅ pytz로 DST 자동화 완료, 2025-01-09)

> **상세 명세**: 더 자세한 내용은 [핵심 통계 로직 명세](#-핵심-통계-로직-명세-quantitative-logic-specification) 및 [코드 수정 주의사항](#️-코드-수정-주의사항) 섹션 참조

---

## 📑 목차

- [핵심 제약 조건](#️-핵심-제약-조건-ai-리팩토링-필수-확인사항)
- [Quick Start](#-quick-start)
- [주요 기능](#-주요-기능)
- [핵심 통계 로직 명세](#-핵심-통계-로직-명세) ← [ARCHITECTURE.md](./ARCHITECTURE.md#-핵심-통계-로직-명세-quantitative-logic-specification)
- [코드 수정 주의사항](#️-코드-수정-주의사항)
- [프로젝트 구조](#️-프로젝트-구조)
- [아키텍처 상세](#-아키텍처-상세) ← [ARCHITECTURE.md](./ARCHITECTURE.md)
- [기술 스택](#️-기술-스택)
- [API 엔드포인트](#-주요-api-엔드포인트)
- [환경 변수](#-환경-변수)
- [모니터링 및 로깅](#-모니터링-및-로깅) ← [ARCHITECTURE.md](./ARCHITECTURE.md#-모니터링-및-로깅-observability)

## 📖 개요

React + FastAPI 기반의 암호화폐 트레이딩 분석 플랫폼입니다.
빠른 UI 응답성과 향상된 사용자 경험을 제공합니다.

## ✨ 주요 기능

| 기능 | 설명 | 주요 파라미터 | 지원 타임프레임 |
|------|------|--------------|----------------|
| **🚀 백테스트** | 8개 전략 백테스트 및 성과 분석 | TP/SL, 레버리지(1-50x), RSI/EMA/MA/ADX | 15m, 30m, 1h, 2h, 4h, 1d |
| **📊 연속 봉패턴 분석** | N연속 양봉/음봉 패턴 분석 | n_streak, direction, RSI threshold | 1d, 3d (시간대별 분석) |
| **📅 주간 패턴 분석** | 주 초반(월-화) 수익률과 주 후반(수-일) 수익률 관계 분석 (하락/상승 자동 판단) | 월요일 시가(API 자동), 화요일 종가(직접 입력), RSI 임계값(직접 입력) | 1d (주간 분석) |
| **📉 볼밴 중단 회귀** | 볼밴 터치 후 중단선 회귀 확률 | start_side, max_bars, RSI range | 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w |
| **🔍 패턴/캔들 통계** | 캔들 패턴 탐지 및 수익률 분석 | pattern type, horizon, TP% | 모든 타임프레임 |
| **📡 전략 스캐너** | 실시간 8개 전략 시그널 모니터링 | strategy_id, direction | 모든 타임프레임 |
| **🔬 하이브리드 전략** | EMA, MACD, RSI, ADX 조합 전략 분석 및 백테스팅 | strategy, tp, sl, max_hold | 1h, 2h, 4h, 1d |
| **🌐 시장 정보** | 실시간 가격, Fear & Greed Index | coin, interval | 실시간 |
| **📓 매매 일지** | 트레이드 기록 및 통계 분석 | entry/exit, PnL, emotion | - |

### 연속 봉패턴 분석 상세

| 모드 | 패턴 | 분석 대상 | 주요 지표 | 특수 기능 |
|------|------|-----------|-----------|-----------|
| **심플 모드** | N연속 양봉/음봉 | C1 (진입일) | C1/C2 확률, 전일 지표 비교 | 뉴욕 시간대별 저점/고점 확률 (1d/3d) |
| **복합 모드** | 다중 캔들 (예: 5양-2음) | C1 (진입일) | RSI 구간별 승률, Bonferroni 보정 | 차트 데이터 시각화, 패턴 품질 점수 |

### 주간 패턴 분석 상세

| 기능 | 설명 | 입력 방식 | 전략 | 주요 지표 |
|------|------|-----------|------|-----------|
| **패턴 분석** | 주 초반(월-화) 수익률과 주 후반(수-일) 수익률 관계 분석 (하락/상승 자동 판단) | 월요일 시가(API 자동), 화요일 종가(직접 입력), RSI 임계값(직접 입력) | 하락: 깊은 하락 필터, 과매도 필터 / 상승: 깊은 상승 필터, 과매수 필터 | 반등 확률(하락) 또는 지속 확률(상승), 기대 수익률, Profit Factor, Sharpe Ratio |
| **백테스팅** | 분석 결과 기반 자동 백테스팅 | 분석 성공 시 자동 실행 | 수요일 시가 진입, 일요일 종가 청산 | 총 거래 수, 반등 확률, 총 수익률, 평균 수익률, 거래 내역 |

**주요 특징:**
- **자동 방향 판단**: 월요일 시가와 화요일 종가를 입력하면 하락/상승을 자동으로 판단
- **하락 케이스**: 화요일 종가 < 월요일 시가 → 주 초반 하락 후 주 후반 반등 확률 분석
- **상승 케이스**: 화요일 종가 > 월요일 시가 → 주 초반 상승 후 주 후반 지속 확률 분석

**사용 흐름:**
1. 사이드바에서 코인 선택 → 월요일 시가 자동 로드
2. 화요일 종가 입력 → 하락/상승 자동 판단 및 임계값 자동 계산
3. RSI 임계값 입력 (기본값: 40)
4. "분석 실행" 클릭 → 분석 및 백테스팅 자동 실행

### 하이브리드 전략 상세

| 기능 | 설명 | 전략 종류 | 주요 지표 |
|------|------|----------|-----------|
| **전략 분석** | 여러 지표를 조합한 전략들의 시그널 발생 통계 분석 | EMA_ADX_Strong, MACD_RSI_Trend, Pure_Trend | EMA, MACD, RSI, ADX, SMA200 |
| **백테스팅** | TP/SL 기반의 현실적인 매매 시뮬레이션 | 선택한 전략 | 승률, Profit Factor, TP/SL 적중률 |
| **라이브 모드** | 완성된 전 봉 기준으로 현재 시점의 각 전략 시그널 상태 확인 | 전체 전략 | 실시간 지표 값 및 조건 충족 여부 |

**주요 특징:**
- **EMA_ADX_Strong**: EMA20 > EMA50 & ADX > 25
- **MACD_RSI_Trend**: MACD > 0 & RSI > 55 & Close > SMA200
- **Pure_Trend**: Close > SMA200
- **라이브 모드**: 진행 중인 봉이 아닌 완성된 전 봉 기준으로 계산
- **공통 지표 함수**: `core/indicators.py`의 `compute_live_indicators()`를 다른 전략에서도 재사용 가능

### 백테스트 전략 목록

| ID | 전략명 | 유형 | 주요 지표 |
|----|--------|------|-----------|
| A1 | Connors | 역추세 | RSI2 |
| A2 | Squeeze | 변동성 | BB, KC |
| A3 | Turtle | 추세 | Donchian |
| A4 | Mean Reversion | 역추세 | BB, RSI |
| B1 | RSI Reversal | 역추세 | RSI |
| B2 | BB Breakout | 돌파 | BB |
| B3 | Engulfing | 패턴 | 캔들 패턴 |

## 🏗️ 프로젝트 구조

> **📖 아키텍처 상세**: 전체 아키텍처, 데이터 흐름도, 알고리즘 흐름도는 [ARCHITECTURE.md](./ARCHITECTURE.md) 참조  
> **📊 연속 봉 분석 상세**: [STREAK_ANALYSIS_FLOW.md](./STREAK_ANALYSIS_FLOW.md) (Simple Mode), [COMPLEX_MODE_FLOW.md](./COMPLEX_MODE_FLOW.md) (Complex Mode)

### 시스템 아키텍처 요약

```
Frontend (React + TypeScript) → HTTP REST API → Backend (FastAPI)
  │                                          │
  ├─ Pages (12개 페이지)                     │
  ├─ Components (재사용 컴포넌트)            │
  ├─ Hooks (공통 로직)                       │
  ├─ Store (Zustand 상태 관리)               │
  └─ API Client (Axios)                      │
                                              │
                                    main.py (FastAPI App)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
            routes/streak.py          routes/stats.py          routes/backtest.py
            routes/market.py          routes/scanner.py        routes/strategies.py
            routes/journal.py         (API Layer)             utils/exceptions.py
                                              │
                                    strategy/ (비즈니스 로직)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
            streak/                  weekly_pattern/            bb_mid/
            ├─ simple_strategy.py   ├─ logic.py                combo_filter/
            ├─ complex_strategy.py   └─ backtest.py            squeeze/
            └─ common.py                                        squeeze/
                                              │
                                    core/ (공유 비즈니스 로직)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
            indicators.py              backtest.py              strategies.py
            support_resistance.py      candle_patterns.py        ...
                                              │
                                    utils/data_service.py (Data Layer)
                                    (Binance API, CSV)
```

### 프론트엔드 구조

**주요 특징:**
- **React 18 + TypeScript**: 타입 안전성과 최신 React 기능 활용
- **Vite**: 빠른 개발 서버 및 빌드
- **Zustand**: 경량 상태 관리 (전역 TP/SL 설정 포함)
- **React Query**: 서버 상태 관리 및 자동 캐싱
- **Plotly.js**: 인터랙티브 차트 시각화
- **Tailwind CSS**: 유틸리티 기반 스타일링

**페이지 구성:**
- 연속 봉패턴 분석 (Simple/Complex 모드)
- 주간 패턴 분석 및 백테스트
- 볼밴 중단 회귀 통계
- 콤보 필터 통계
- 멀티 타임프레임 스퀴즈 분석
- 패턴/전략 스캐너
- 매매 일지

**공통 패턴:**
- `usePageCommon()`: 페이지 공통 로직 (language, labels, timeframes)
- `useAnalysisMutation()`: 분석 API 호출 패턴 통일
- `DataSourceToggle`: API/CSV 데이터 소스 선택

### 백엔드 구조

**주요 특징:**
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **모듈화된 라우터**: 기능별로 분리된 API 엔드포인트 (7개 라우터 모듈)
- **전략 패턴**: 비즈니스 로직을 `strategy/` 디렉토리로 분리
- **공통 유틸리티**: `utils/` 디렉토리에 공통 로직 통합
- **공유 코어 모듈**: `core/` 디렉토리에 공통 비즈니스 로직

**API 레이어 구조:**
- `routes/`: 얇은 API 레이어 (요청 검증, 파라미터 변환)
- `strategy/`: 비즈니스 로직 (분석 알고리즘)
- `core/`: 공유 비즈니스 로직 (지표 계산, 백테스트 엔진)
- `utils/`: 공통 유틸리티 (데이터 소스 접근, 데이터 로딩, 에러 처리)
- `services/`: 서비스 레이어 (통계 계산, 패턴 로직)

**데이터 소스:**
- Binance API (CCXT 라이브러리)
- CSV 파일 (히스토리컬 데이터)
- 메모리 캐싱 (성능 최적화)

### 파일 구조

```
my_quant_V2/
├── backend/                 # FastAPI 백엔드
│   ├── main.py             # 메인 앱 (Router 등록 및 CORS 설정)
│   ├── __init__.py         # 패키지 초기화 (경로 설정 통합 관리)
│   ├── routes/             # 분리된 API 라우터 (모듈화된 엔드포인트)
│   │   ├── backtest.py    # 백테스트 API (/api/backtest*, /api/backtest-advanced)
│   │   ├── journal.py     # 매매 일지 API (/api/journal)
│   │   ├── market.py      # 시장 데이터 API (/api/market/*, /api/support-resistance/*)
│   │   ├── scanner.py     # 스캐너 API (/api/scanner, /api/pattern-scanner)
│   │   ├── stats.py       # 통계 분석 API (/api/bb-mid, /api/combo-filter, /api/multi-tf-squeeze)
│   │   ├── strategies.py   # 전략 정보 API (/api/strategies, /api/strategy-info/*, /api/presets)
│   │   └── streak.py      # 연속 봉패턴 분석 API (/api/streak-analysis)
│   ├── utils/              # 유틸리티 모듈
│   │   ├── data_service.py # 데이터 소스 접근 (Binance API, CSV)
│   │   ├── data_loader.py  # 공통 데이터 로딩 함수 (CSV 우선, API 폴백)
│   │   ├── exceptions.py  # 전역 예외 처리기 (표준 에러 응답 스키마)
│   │   └── decorators.py  # 공통 API 에러 처리 데코레이터
│   ├── services/           # 서비스 레이어
│   │   ├── statistics.py  # 백테스트 통계 계산 (Sharpe, Sortino, MDD, Monte Carlo)
│   │   └── pattern_logic.py # 패턴 감지 및 통계 계산
│   ├── strategy/           # 전략 모듈 (비즈니스 로직)
│   │   ├── common.py       # 공통 통계 함수 (re-export from streak/common)
│   │   ├── streak/         # 연속 봉패턴 분석 전략
│   │   │   ├── simple_strategy.py  # 심플 모드
│   │   │   ├── complex_strategy.py # 복합 모드
│   │   │   ├── common.py           # 공통 유틸리티 (메인 소스)
│   │   │   └── statistics.py       # 통계 함수 (단일 소스)
│   │   ├── weekly_pattern/ # 주간 패턴 분석 전략
│   │   │   ├── logic.py    # 주간 패턴 분석 로직
│   │   │   ├── backtest.py # 주간 패턴 백테스팅 로직
│   │   │   ├── indicators.py # 기술적 지표 계산
│   │   │   └── validation.py # 데이터 검증
│   │   ├── hybrid/         # 하이브리드 전략 (EMA, MACD, RSI, ADX)
│   │   │   ├── logic.py    # 전략 분석 및 라이브 모드 로직
│   │   │   └── backtest.py # 백테스팅 로직
│   │   ├── bb_mid/         # 볼밴 중단 회귀 통계
│   │   │   └── logic.py
│   │   ├── combo_filter/   # 콤보 필터 통계
│   │   │   └── logic.py
│   │   └── squeeze/        # 멀티 타임프레임 스퀴즈
│   │       └── logic.py
│   ├── models/             # Pydantic 모델
│   │   └── request.py      # API 요청/응답 모델
│   ├── tests/              # 테스트 코드
│   │   ├── conftest.py     # pytest 설정
│   │   └── test_c1_extraction.py  # C1 날짜 추출 검증 테스트
│   ├── pytest.ini          # pytest 설정 파일
│   └── requirements.txt    # Python 의존성
│
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── api/           # API 클라이언트
│   │   │   └── client.ts  # Axios 기반 API 클라이언트
│   │   ├── components/    # 공통 컴포넌트
│   │   │   ├── Chart.tsx              # Plotly 차트 컴포넌트
│   │   │   ├── DataSourceToggle.tsx   # API/CSV 토글 컴포넌트
│   │   │   ├── Layout.tsx             # 레이아웃 컴포넌트
│   │   │   ├── MetricCard.tsx         # 메트릭 카드 컴포넌트
│   │   │   ├── ParamsPanel.tsx        # 파라미터 패널 컴포넌트
│   │   │   ├── Sidebar.tsx            # 사이드바 컴포넌트
│   │   │   ├── Skeleton.tsx           # 로딩 스켈레톤 컴포넌트
│   │   │   ├── StrategyExplainer.tsx  # 전략 설명 컴포넌트
│   │   │   └── TradesTable.tsx        # 거래 내역 테이블 컴포넌트
│   │   ├── hooks/         # 커스텀 훅 (공통 로직 추출)
│   │   │   ├── usePageCommon.ts       # 페이지 공통 훅 (language, labels, timeframes 등)
│   │   │   └── useAnalysisMutation.ts # 분석 API Mutation 훅 (에러 처리, 파라미터 동기화)
│   │   ├── pages/         # 페이지 컴포넌트
│   │   │   ├── StreakAnalysisPage.tsx      # 연속 봉패턴 분석 페이지
│   │   │   ├── WeeklyPatternPage.tsx       # 주간 패턴 분석 페이지
│   │   │   ├── BBMidPage.tsx               # 볼밴 중단 회귀 페이지
│   │   │   ├── ComboFilterPage.tsx          # 콤보 필터 페이지
│   │   │   ├── MultiTFSqueezePage.tsx       # 멀티 타임프레임 스퀴즈 페이지
│   │   │   ├── PatternPage.tsx              # 패턴 통계 페이지
│   │   │   ├── PatternScannerPage.tsx       # 패턴 스캐너 페이지
│   │   │   ├── StrategyScannerPage.tsx     # 전략 스캐너 페이지
│   │   │   ├── JournalPage.tsx              # 매매 일지 페이지
│   │   │   ├── BacktestPage.tsx             # 기본 백테스트 페이지 (현재 숨김)
│   │   │   └── AdvancedBacktestPage.tsx    # 고급 백테스트 페이지 (현재 숨김)
│   │   ├── store/         # 상태 관리 (Zustand)
│   │   │   ├── useStore.ts  # 전역 상태 (TP/SL, use_csv 설정 포함)
│   │   │   └── labels.ts    # 다국어 라벨
│   │   ├── types/         # TypeScript 타입 정의
│   │   │   └── index.ts
│   │   ├── App.tsx        # 메인 앱 컴포넌트 (라우팅 설정)
│   │   ├── main.tsx       # 진입점
│   │   └── index.css      # 전역 스타일
│   ├── public/            # 정적 파일
│   │   └── diamond.svg    # 로고
│   ├── package.json       # npm 의존성
│   ├── vite.config.ts     # Vite 설정
│   ├── tailwind.config.js # Tailwind CSS 설정
│   ├── tsconfig.json      # TypeScript 설정
│   └── .eslintrc.cjs      # ESLint 설정
│
├── core/                    # 핵심 비즈니스 로직 (공유 모듈)
│   ├── indicators.py       # 기술적 지표 계산 (RSI, ADX, MA, BB, MACD 등)
│   │                        # - compute_live_indicators(): 실시간 지표 계산 (하이브리드 전략 등에서 재사용)
│   │                        # - get_latest_indicator_values(): 최신 봉 지표 값 추출
│   ├── backtest.py         # 백테스트 엔진
│   ├── strategies.py       # 전략 정의 (8개 전략)
│   ├── support_resistance.py # 지지/저항 계산
│   ├── candle_patterns.py  # 캔들 패턴 탐지
│   ├── charts.py           # 차트 유틸리티
│   ├── journal.py          # 매매 일지 로직
│   ├── presets.py          # 프리셋 관리
│   └── ...
│
├── binance_klines/          # 히스토리컬 데이터 (CSV)
├── start.sh                 # 개발 서버 시작 스크립트
├── presets.json             # 저장된 프리셋
├── README.md                # 프로젝트 메인 문서
├── ARCHITECTURE.md          # 아키텍처 상세 문서
├── API.md                   # API 명세 문서
├── INSTALL.md               # 설치 가이드
└── .github/workflows/       # CI/CD 워크플로우
    └── test.yml
```

### 프론트엔드 상세

**기술 스택:**
- **React 18**: 함수형 컴포넌트 및 Hooks 기반
- **TypeScript 5.3**: 타입 안전성 보장
- **Vite 5**: 빠른 개발 서버 및 빌드
- **Tailwind CSS 3.4**: 유틸리티 기반 스타일링
- **Zustand 4.4**: 경량 상태 관리 (전역 설정 포함)
- **React Query (TanStack Query) 5.17**: 서버 상태 관리 및 캐싱
- **Plotly.js 2.28**: 인터랙티브 차트 라이브러리
- **React Router 6.21**: 클라이언트 사이드 라우팅
- **Axios 1.6**: HTTP 클라이언트

**주요 컴포넌트:**
- `Chart.tsx`: Plotly 기반 차트 컴포넌트 (확대/축소, 드래그 지원)
- `MetricCard.tsx`: 메트릭 카드 컴포넌트 (승률, 수익률 등)
- `Sidebar.tsx`: 사이드바 네비게이션
- `ParamsPanel.tsx`: 파라미터 입력 패널
- `TradesTable.tsx`: 거래 내역 테이블
- `DataSourceToggle.tsx`: API/CSV 데이터 소스 선택

**상태 관리:**
- 전역 상태: Zustand를 통한 전역 설정 관리
  - `backtestParams`: TP/SL, use_csv, 전략 설정 등
  - `selectedCoin`: 선택된 코인
  - `language`: 선택된 언어 (ko/en)
- 서버 상태: React Query를 통한 API 응답 캐싱 및 자동 새로고침

**공통 훅:**
- `usePageCommon()`: 페이지 공통 로직 (language, labels, timeframes)
- `useAnalysisMutation()`: 분석 API 호출 패턴 통일

### 백엔드 상세

**기술 스택:**
- **FastAPI 0.109**: 고성능 비동기 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic 2.5**: 데이터 검증 및 직렬화
- **Pandas 2.0**: 데이터 처리 및 분석
- **NumPy 1.24**: 수치 계산
- **CCXT 4.0**: 암호화폐 거래소 API (Binance)
- **SciPy 1.11**: 과학 계산 (통계 분석)
- **pytz 2023.3**: 시간대 처리 (EST/EDT 변환)

**아키텍처 패턴:**
- **모듈화된 라우터**: 기능별로 분리된 API 엔드포인트 (7개 라우터 모듈)
- **전략 패턴**: 비즈니스 로직을 `strategy/` 디렉토리로 분리
- **공통 유틸리티**: `utils/` 디렉토리에 공통 로직 통합
- **공유 코어 모듈**: `core/` 디렉토리에 공통 비즈니스 로직

**주요 모듈:**
- `routes/`: API 레이어 (요청 검증, 파라미터 변환)
- `strategy/`: 비즈니스 로직 (분석 알고리즘)
  - `streak/`: 연속 봉패턴 분석 (Simple/Complex 모드)
  - `weekly_pattern/`: 주간 패턴 분석
  - `bb_mid/`: 볼밴 중단 회귀 통계
  - `combo_filter/`: 콤보 필터 통계
  - `squeeze/`: 멀티 타임프레임 스퀴즈
- `core/`: 공유 비즈니스 로직
  - `indicators.py`: 기술적 지표 계산
  - `backtest.py`: 백테스트 엔진
  - `strategies.py`: 전략 정의
- `utils/`: 공통 유틸리티
  - `data_loader.py`: 데이터 로딩 통합
  - `exceptions.py`: 예외 처리
  - `decorators.py`: API 데코레이터

**데이터 소스:**
- Binance API (CCXT 라이브러리) - 실시간 데이터
- CSV 파일 - 히스토리컬 데이터
- 메모리 캐싱 - 성능 최적화

## 🛠️ 기술 스택

### Frontend
- **React 18** - UI 라이브러리
- **TypeScript 5.3** - 타입 안전성
- **Vite 5** - 빌드 도구 및 개발 서버
- **Tailwind CSS 3.4** - 유틸리티 기반 스타일링
- **Zustand 4.4** - 경량 상태 관리 (전역 TP/SL 설정 포함)
- **React Query (TanStack Query) 5.17** - 서버 상태 관리 및 캐싱
- **Plotly.js 2.28** - 인터랙티브 차트 라이브러리
- **React Router 6.21** - 클라이언트 사이드 라우팅
- **Axios 1.6** - HTTP 클라이언트
- **Lucide React** - 아이콘 라이브러리
- **date-fns 3.2** - 날짜 유틸리티

### Backend
- **FastAPI 0.109** - 고성능 Python 웹 프레임워크
- **Uvicorn** - ASGI 서버
- **Pydantic 2.5** - 데이터 검증 및 직렬화
- **Pandas 2.0** - 데이터 처리 및 분석
- **NumPy 1.24** - 수치 계산
- **CCXT 4.0** - 암호화폐 거래소 API (Binance)
- **SciPy 1.11** - 과학 계산 (통계 분석)
- **pytz 2023.3** - 시간대 처리 (EST/EDT 변환)
- **pytest 7.4** - 테스트 프레임워크

## 📡 주요 API 엔드포인트

> **상세 명세**: 전체 API 명세는 [API.md](./API.md)를 참조하세요.

### 전체 API 엔드포인트 목록

| Method | Endpoint | 설명 | 입력/출력 타입 |
|--------|----------|------|----------------|
| GET | `/api/market/prices` | 시장 가격 조회 | JSON |
| GET | `/api/market/fear-greed` | Fear & Greed Index | JSON |
| GET | `/api/market/timeframes/{coin}` | 사용 가능한 타임프레임 | JSON |
| GET | `/api/market/ohlcv/{coin}/{interval}` | OHLCV 데이터 | JSON |
| GET | `/api/strategies` | 전략 목록 | JSON |
| GET | `/api/strategy-info/{id}` | 전략 설명 | JSON |
| POST | `/api/backtest` | 백테스트 실행 | BacktestParams → BacktestResult |
| POST | `/api/backtest-advanced` | 고급 백테스트 | AdvancedBacktestParams → AdvancedBacktestResult |
| POST | `/api/streak-analysis` | 연속 봉패턴 분석 | StreakAnalysisParams → StreakAnalysisResult |
| POST | `/api/weekly-pattern` | 주간 패턴 분석 | WeeklyPatternParams → WeeklyPatternResult |
| POST | `/api/weekly-pattern-backtest` | 주간 패턴 백테스트 | WeeklyPatternBacktestParams → WeeklyPatternBacktestResult |
| POST | `/api/bb-mid` | 볼밴 중단 회귀 통계 | BBMidParams → BBMidResult |
| POST | `/api/combo-filter` | 콤보 필터 통계 | ComboFilterParams → ComboFilterResult |
| POST | `/api/multi-tf-squeeze` | 멀티 타임프레임 스퀴즈 분석 | MultiTFSqueezeParams → MultiTFSqueezeResult |
| POST | `/api/hybrid-analysis` | 하이브리드 전략 분석 | HybridAnalysisParams → HybridAnalysisResult |
| POST | `/api/hybrid-backtest` | 하이브리드 전략 백테스팅 | HybridBacktestParams → HybridBacktestResult |
| POST | `/api/hybrid-live` | 하이브리드 전략 라이브 모드 | HybridLiveModeParams → HybridLiveModeResult |
| GET | `/api/support-resistance/{coin}/{interval}` | 지지/저항 레벨 | JSON |
| POST | `/api/scanner` | 전략 스캐너 | ScannerParams → ScannerResult |
| POST | `/api/pattern-scanner` | 패턴 스캐너 | PatternScanParams → PatternScanResult |
| GET | `/api/presets` | 프리셋 목록 | JSON |
| POST | `/api/presets` | 프리셋 저장 | PresetSaveRequest → JSON |
| DELETE | `/api/presets/{name}` | 프리셋 삭제 | JSON |
| GET | `/api/journal` | 매매 일지 조회 | JSON |
| POST | `/api/journal` | 매매 일지 추가 | JournalEntry → JSON |
| DELETE | `/api/journal/{entry_id}` | 매매 일지 삭제 | JSON |

## 🚀 Quick Start

```bash
chmod +x start.sh && ./start.sh
```

**접속**: Frontend http://localhost:5173 | Backend http://localhost:8000 | API Docs http://localhost:8000/docs

> 📦 **상세 설치 방법**: [INSTALL.md](./INSTALL.md) 참조


## 🎨 UI 특징

- **다크 테마**: 트레이딩에 최적화된 어두운 색상 테마
- **반응형 디자인**: 데스크톱 및 태블릿 지원
- **애니메이션**: 부드러운 전환 효과
- **인터랙티브 차트**: 확대/축소, 드래그 지원 (Plotly)
- **실시간 업데이트**: React Query 기반 자동 새로고침

## 📊 모니터링 및 로깅

> **현재 상태**: 기본 로깅만 사용 중 (Python `logging` 모듈)
> **상세 내용**: 운영 및 모니터링 관련 상세 내용은 [ARCHITECTURE.md](./ARCHITECTURE.md#-모니터링-및-로깅-observability)를 참조하세요.

## 📊 지원 타임프레임

- **분봉**: 15m, 30m
- **시간봉**: 1h, 2h, 4h, 8h, 12h
- **일봉**: 1d, 3d
- **주봉**: 1w

## 🔧 환경 변수

### Frontend (.env)
```env
# API 서버 URL
VITE_API_URL=http://localhost:8000
```

### Backend (.env)

백엔드 실행에 필수적인 환경 변수:

```env
# CORS 설정 (프론트엔드 도메인 허용)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 디버그 모드 설정 (연속 봉패턴 분석 디버그 로그)
DEBUG_STREAK_ANALYSIS=false  # true로 설정 시 상세 로그 출력

# 데이터 경로 설정 (CSV 파일 경로)
# 기본값: 프로젝트 루트/binance_klines
BINANCE_DATA_PATH=./binance_klines

# 캐시 설정
CACHE_TTL=300  # 캐시 TTL (초), 기본값: 300초
CACHE_MAX_SIZE=100  # 최대 캐시 항목 수, 기본값: 100

# API 타임아웃 설정
API_TIMEOUT=30  # API 요청 타임아웃 (초), 기본값: 30초

# 타임존 설정 (시간대별 분석용)
TIMEZONE_OFFSET=-5  # EST 시간대 오프셋, 기본값: -5
```

### 환경 변수 상세 설명

- **DEBUG_STREAK_ANALYSIS**: `true`로 설정 시 연속 봉패턴 분석의 상세 로그가 출력됩니다. 성능 분석이나 디버깅 시 유용합니다.
- **BINANCE_DATA_PATH**: CSV 파일이 저장된 경로를 지정합니다. 상대 경로 또는 절대 경로 모두 지원합니다.
- **CACHE_TTL**: 캐시된 분석 결과의 유효 기간(초)입니다. 데이터가 자주 업데이트되는 경우 값을 줄이세요.
- **TIMEZONE_OFFSET**: 시간대별 분석에서 사용하는 EST 시간대 오프셋입니다. 일광절약시간(DST) 적용 시 `-4`로 변경해야 할 수 있습니다.

## 📦 배포

```bash
cd frontend && npm run build
```

빌드된 파일은 `dist/` 폴더에 생성됩니다. 상세 배포 방법은 [INSTALL.md](./INSTALL.md#프로덕션-빌드) 참조.



> **중요**: 이 섹션은 [핵심 제약 조건](#️-핵심-제약-조건-ai-리팩토링-필수-확인사항) 섹션의 상세 확장입니다.  
> 통계적 정확성 및 비즈니스 로직의 핵심이므로, 리팩토링이나 최적화 시 절대 변경하지 마세요.

### 🚫 절대 변경 금지 사항

1. **C1 날짜 추출 로직**
   - **위치**: `simple_strategy.py` 236-246줄, `complex_strategy.py` 380-389줄
   - **금지 사항**: 
     - 패턴 완성 시점(`target_cases.index`, `matched_patterns.index`)을 직접 분석하는 것으로 변경 금지
     - 항상 "다음 봉(C1)"을 분석 대상으로 사용해야 함
   - **이유**: 시간대별 분석은 C1(진입일)을 기준으로 해야 정확함

2. **`valid_date_count` 로직**
   - **위치**: `common.py` - `calculate_intraday_distribution()`
   - **금지 사항**: 
     - 저점과 고점이 다른 EST 구간에 있는 날짜만 카운트하는 로직 제거 금지
     - `valid_date_count` 대신 전체 날짜 수를 사용하는 것으로 변경 금지
   - **이유**: 같은 구간에 저점/고점이 모두 있는 날을 포함하면 확률 계산이 왜곡됨

3. **Wilson Score Interval 공식**
   - **위치**: `common.py` - `wilson_confidence_interval()`
   - **금지 사항**: 
     - 공식 변경 또는 단순화 금지
     - $z = 1.96$ (95% 신뢰수준) 변경 금지
     - 샘플 수 < 10일 경우 'Low Reliability' 표시 로직 제거 금지
   - **이유**: 소수 샘플 편향 방지를 위한 필수 통계 기법

4. **EST 시간대 변환 로직**
   - **위치**: `common.py` - `calculate_intraday_distribution()` 내부
   - **구현**: ✅ `pytz.timezone('America/New_York')` 사용 (DST 자동 처리)
   - **금지 사항**: 
     - UTC → EST/EDT 변환 로직 제거 또는 변경 금지
     - pytz 사용 제거 금지
     - 4시간 구간(0-5) 인덱스 계산 로직 변경 금지
   - **이유**: 뉴욕 거래 시간대 정확한 매핑 필수, DST 자동 처리로 운영 리스크 제거

5. **Bonferroni 보정 적용**
   - **위치**: `common.py` - `analyze_interval_statistics()`
   - **금지 사항**: 
     - 보정 로직 제거 금지
     - 보정 없이 원래 유의수준(0.05)만 사용하는 것으로 변경 금지
   - **이유**: 다중 비교 시 False Positive 방지 필수

6. **데이터 정규화 (DatetimeIndex)**
   - **위치**: `common.py` - `normalize_indices()`
   - **금지 사항**: 
     - DatetimeIndex 강제 요구사항 제거 금지
     - 인덱스 타입 검증 로직 생략 금지
   - **이유**: 인덱스 기반 접근 시 타입 불일치로 인한 버그 방지

### ⚠️ 주의하여 수정 가능한 사항

1. **C1 추출 로직 중복 제거**: `common.py`에 유틸리티 함수로 추출 가능 (단, 로직 변경 금지)
2. **에러 처리 강화**: 예외 처리 로직은 개선 가능
3. **성능 최적화**: 벡터화된 연산으로 개선 가능 (단, 결과값 동일성 보장 필수)

### 📋 리팩토링 체크리스트

코드를 수정하기 전에 다음을 확인하세요:

- [ ] 수학적 정의(공식)를 변경하지 않았는가?
- [ ] C1 날짜 추출 로직이 "다음 봉"을 분석하는가?
- [ ] `valid_date_count` 로직이 유지되는가?
- [ ] Wilson Score Interval 공식이 변경되지 않았는가?
- [ ] Bonferroni 보정이 적용되는가?
- [x] EST/EDT 시간대 변환이 정확한가? (✅ pytz로 DST 자동화 완료)
- [ ] DatetimeIndex 정규화가 수행되는가?

---



## 🧮 핵심 통계 로직 명세

> **상세 명세**: 수학 공식 및 통계 로직 상세 내용은 [ARCHITECTURE.md](./ARCHITECTURE.md#-핵심-통계-로직-명세-quantitative-logic-specification)를 참조하세요.

## 🧪 테스트

### C1 날짜 추출 검증 테스트

핵심 제약 조건인 C1 날짜 추출 로직의 정확성을 검증하는 테스트입니다.

**실행 방법**:
```bash
cd backend
source venv/bin/activate
pytest tests/test_c1_extraction.py -v
```

**테스트 항목**:
- C1 날짜가 항상 패턴 완성 시점의 다음 날짜(T+1)인지 검증
- 인덱스 범위 체크가 올바르게 수행되는지 검증
- DatetimeIndex 정규화 후에도 올바르게 작동하는지 검증
- 미래 참조 오류 방지 검증
- Simple Mode와 Complex Mode 통합 테스트

### 통계 로직 단위 테스트

핵심 통계 함수들의 정확성을 검증하는 테스트입니다.

**실행 방법**:
```bash
cd backend
source venv/bin/activate
pytest tests/test_statistics.py -v
```

**테스트 항목**:
- `wilson_confidence_interval()`: Wilson Score 신뢰구간 계산 (7개 테스트)
- `bonferroni_correction()`: Bonferroni 다중 비교 보정 (4개 테스트)
- `calculate_binomial_pvalue()`: 이항검정 p-value 계산 (4개 테스트)
- `analyze_interval_statistics()`: 구간별 통계 분석 (3개 테스트)
- `calculate_intraday_distribution()`: 시간대별 분포 계산 (3개 테스트)

**총 21개 테스트 케이스**

### Core Guard 검증

`core/` 디렉토리가 `backend/`를 import하지 않는지 검증하는 스크립트입니다.

**실행 방법**:
```bash
python3 scripts/check_core_imports.py
```

**목적**: `core/` 디렉토리는 독립 라이브러리로 유지되어야 하며, `backend/` 또는 `frontend/`를 import하면 안 됩니다.

**중요**: 리팩토링 전/후 반드시 모든 테스트가 통과해야 합니다.

## 📝 개발 노트

- 백엔드 API는 FastAPI의 라우터를 사용하여 모듈화됨
- 연속 봉패턴 분석은 전략 패턴으로 리팩토링됨 (strategy/ 디렉토리)
- 프론트엔드는 React Query를 사용하여 서버 상태 관리
- 캐싱 전략은 TTL 기반으로 구현됨
- **전역 설정 통합**: TP/SL, use_csv 설정은 Zustand의 `backtestParams`를 통해 전역 관리되며, 한 페이지에서 변경 시 모든 페이지에 자동 동기화됨
- **코드 최적화**: 공통 데이터 로딩 함수(`utils/data_loader.py`), 공통 Hook(`hooks/usePageCommon.ts`, `hooks/useAnalysisMutation.ts`)을 통한 중복 코드 제거 (~150줄 감소)
- **테스트 코드**: 
  - C1 날짜 추출 검증 테스트 (`tests/test_c1_extraction.py`) - 리팩토링 시 회귀 방지
  - 통계 로직 단위 테스트 (`tests/test_statistics.py`) - 21개 테스트 케이스
  - Core Guard 스크립트 (`scripts/check_core_imports.py`) - 아키텍처 무결성 검증
- **백엔드 중복 제거 (2026-01)**: 
  - 미사용 파일 삭제: `strategy/simple_strategy.py` (507줄), `strategy/weekly_pattern/logic_improved.py` (435줄), `strategy/complex_strategy.py` (747줄)
  - `strategy/common.py` 중복 제거: 718줄 → 295줄 (60% 감소)
  - 통계 함수 통합: `strategy/streak/statistics.py`를 단일 소스로 사용
  - 총 코드 감소: ~1,700줄
- **코드 품질 개선 (2026-01-20)**:
  - 중복 함수 통합: `_calculate_indicators` 함수를 `common.py`로 이동하여 중복 제거 (27줄 감소)
  - 불필요한 import 제거: `datetime`, `timedelta`, `pytz`, `numpy` 등 사용하지 않는 import 정리
  - 버그 수정: 구간별 승률 분석에서 잘못된 타겟 시리즈 사용 문제 수정 (Simple Mode)
  - 복합 분석 개선: C1 양봉/음봉 확률이 최상위 레벨에 표시되도록 수정
  - 기능 제거: MA Cross 통계 기능 완전 제거 (Combo Filter로 대체 가능)
- **하이브리드 전략 추가 (2026-01)**:
  - 하이브리드 전략 분석 기능 추가 (EMA, MACD, RSI, ADX 조합)
  - 하이브리드 전략 백테스팅 기능 추가 (TP/SL 기반 현실적 시뮬레이션)
  - 하이브리드 전략 라이브 모드 추가 (완성된 전 봉 기준 시그널 확인)
  - 라이브 모드 지표 계산 함수를 `core/indicators.py`로 이동 (다른 전략에서도 재사용 가능)
  - 프론트엔드 하이브리드 전략 페이지 추가 (라이브 모드 UI 포함)
  - 중복 코드 제거: `_prepare_indicators_and_signals()` 공통 함수 추가

## 🤝 기여

버그 리포트, 기능 제안, PR을 환영합니다!

## 📄 라이선스

MIT License

---

**💎 월젬의 퀀트 마스터** - 트레이딩 분석의 새로운 기준
