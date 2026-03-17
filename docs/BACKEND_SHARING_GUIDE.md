# 백엔드 공유 가이드 (Backend Sharing Guide)

> 다른 AI와 백엔드를 공유할 때 필요한 핵심 정보를 요약한 문서입니다.

## 📋 프로젝트 개요

**Quant Master Backend** - 암호화폐 트레이딩 분석을 위한 FastAPI 백엔드

- **프레임워크**: FastAPI 0.109
- **언어**: Python 3.9+
- **주요 라이브러리**: Pandas, NumPy, SciPy, CCXT, Pydantic
- **포트**: 8000 (기본값)

## 🚨 절대 변경 금지 사항 (Critical Constraints)

### 1. DatetimeIndex 정규화 (시스템 로직 최상단)
- **위치**: `backend/strategy/streak/common.py` - `normalize_indices()`
- **규칙**: 모든 분석용 DataFrame은 반드시 `DatetimeIndex`를 보유해야 함
- **금지**: 인덱스 타입 검증 로직 생략, 다른 인덱스 타입 허용
- **이유**: 인덱스 기반 접근 시 타입 불일치로 인한 버그 방지

### 2. C1 날짜 추출 로직
- **패턴 완성 시점 ≠ 분석 대상**: 패턴 완성 시점이 아닌 **다음 봉(C1, 진입일)**을 분석해야 함
- **위치**: 
  - `backend/strategy/streak/simple_strategy.py` (236-246줄)
  - `backend/strategy/streak/complex_strategy.py` (380-389줄)
- **금지**: 패턴 완성 시점을 직접 분석하는 것으로 변경 금지

### 3. Wilson Score Interval 공식
- **위치**: `backend/strategy/streak/statistics.py` - `wilson_confidence_interval()`
- **공식**: $z = 1.96$ (95% 신뢰수준) 기준
- **금지**: 공식 변경, $z = 1.96$ 변경, 'Low Reliability' 로직 제거 금지

### 4. Bonferroni 보정
- **위치**: `backend/strategy/streak/statistics.py` - `analyze_interval_statistics()`
- **공식**: $\alpha_{adjusted} = \frac{\alpha}{n_{comparisons}}$
- **high_prob 최소 샘플 기본값**: `DEFAULT_HIGH_PROB_MIN_SAMPLE = 10` (예외 케이스만 호출부에서 명시 override)
- **금지**: 보정 로직 제거 금지

### 5. EST 시간대 변환
- **위치**: `backend/strategy/streak/statistics.py` - `calculate_intraday_distribution()`
- **구현**: `pytz.timezone('America/New_York')` 사용 (DST 자동 처리)
- **금지**: UTC → EST/EDT 변환 로직 제거/변경 금지

## 🏗️ 백엔드 구조

### 주요 디렉토리

```
backend/
├── main.py                 # FastAPI 앱 진입점
├── modules/                # 도메인별 router/service/schema (정식 위치)
│   ├── ai_lab/            # /api/ai/research
│   ├── backtest/          # /api/backtest*
│   ├── market/            # /api/market/*, /api/timeframes/*, /api/ohlcv/*
│   ├── scanner/           # /api/scanner, /api/pattern-scanner
│   ├── streak/            # /api/streak-analysis*
│   ├── stats/             # /api/trend-indicators, /api/bb-mid, /api/combo-filter, /api/hybrid-*
│   ├── preset/            # /api/presets*
│   ├── journal/           # /api/journal*
│   ├── support_resistance/# /api/support-resistance/*
│   └── strategy_info/     # /api/strategy-info/*
├── strategy/               # 비즈니스 로직 (전략 모듈)
│   ├── streak/            # 연속 봉패턴 분석
│   │   ├── simple_strategy.py
│   │   ├── complex_strategy.py
│   │   ├── common.py      # facade (re-export only, 통계 함수 미포함)
│   │   ├── cache_ops.py   # 캐시 관련 로직
│   │   ├── data_ops.py    # 데이터 로드/정규화/지표 계산
│   │   ├── pattern_ops.py # 패턴 매칭/품질 분석
│   │   ├── json_utils.py  # JSON 직렬화 유틸
│   │   └── statistics.py  # 통계/수치 헬퍼 단일 소스 (SSOT)
│   ├── hybrid/            # 하이브리드 전략 (SMA, MACD, RSI, ADX)
│   ├── bb_mid/           # 볼밴 중단 회귀
│   ├── combo_filter/     # 콤보 필터
├── utils/                 # 공통 유틸리티
│   ├── data_service.py   # 데이터 소스 접근 (Binance API, CSV)
│   ├── data_loader.py    # 공통 데이터 로딩 함수
│   ├── cache.py          # 메모리 캐시
│   └── decorators.py     # API 에러 처리 데코레이터
├── services/              # 공용 서비스
│   ├── ai_clients.py      # LLM provider adapter
│   ├── pattern_logic.py   # 패턴 감지 유틸
│   └── statistics.py      # 고급 통계 계산
├── core/                  # 공유 비즈니스 로직 (프로젝트 루트)
│   ├── indicators.py     # 기술적 지표 계산 (RSI, ADX, MA, BB, MACD 등)
│   ├── backtest.py       # 백테스트 엔진
│   └── strategies.py     # 전략 정의
└── config/               # 설정 파일
    ├── settings.py       # 앱 설정 (CORS 등)
    └── strategies.yaml   # 전략 메타데이터
```

## 📡 주요 API 엔드포인트

### 연속 봉패턴 분석
- **POST** `/api/streak-analysis`
- **파라미터**: `coin`, `interval`, `n_streak`, `direction`, `use_complex_pattern`, `complex_pattern`, `rsi_threshold`
- **로직**: `backend/strategy/streak/` 모듈

### 하이브리드 전략
- **POST** `/api/hybrid-analysis` - 전략 분석
- **POST** `/api/hybrid-backtest` - 백테스팅
- **POST** `/api/hybrid-live` - 라이브 모드 (완성된 전 봉 기준)
- **파라미터**: `coin`, `interval`, `strategy`, `tp`, `sl`, `max_hold`
- **로직**: `backend/strategy/hybrid/` 모듈
- **지표 계산**: `core/indicators.py` - `compute_live_indicators()` (공통 함수)

### 볼밴 중단 회귀
- **POST** `/api/bb-mid`
- **로직**: `backend/strategy/bb_mid/` 모듈

### 콤보 필터
- **POST** `/api/combo-filter`
- **로직**: `backend/strategy/combo_filter/` 모듈

### 백테스트
- **POST** `/api/backtest`
- **POST** `/api/backtest-advanced`
- **엔진**: `core/backtest.py`

## 🔑 핵심 모듈 설명

### 1. 데이터 로딩 (`utils/data_loader.py`)
- CSV 우선, API 폴백 방식
- 캐싱 지원 (TTL 기반)
- DatetimeIndex 정규화 포함

### 2. 지표 계산 (`core/indicators.py`)
- **공통 함수**: `compute_live_indicators()` - SMA, MACD, RSI, ADX 계산
- 하이브리드 전략 및 다른 전략에서 재사용 가능
- Wilder's Smoothing 적용

### 3. 전략 시그널 생성 (`strategy/hybrid/logic.py`)
- `generate_strategy_signals()` - 여러 전략 시그널 생성
- 전략:
  - `SMA_ADX_Strong`: SMA20 > SMA50 & ADX > 25
  - `MACD_RSI_Trend`: MACD > 0 & RSI > 55 & Close > SMA200
  - `Pure_Trend`: Close > SMA200

### 4. 공통 통계 함수 (`strategy/common.py`)
- `calculate_profit_factor()` - Profit Factor 계산
- `calculate_sharpe_ratio_unified()` - Sharpe Ratio
- `calculate_max_drawdown_unified()` - Maximum Drawdown
- `calculate_t_test_unified()` - t-test

### 5. 캐싱 (`utils/cache.py`)
- TTL 기반 메모리 캐시
- 데이터 캐시: 5분 TTL
- 분석 결과 캐시: 무제한 (수동 삭제)

## 🔧 의존성

### 필수 패키지 (`requirements.txt`)
```
fastapi>=0.109.0
uvicorn[standard]
pydantic>=2.5.0
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.11.0
ccxt>=4.0.0
pytz>=2023.3
```

## ⚙️ 설정

### 환경 변수 (`config/settings.py`)
- `CORS_ORIGINS`: CORS 허용 도메인
- `DEBUG_STREAK_ANALYSIS`: 디버그 모드
- `BINANCE_DATA_PATH`: CSV 데이터 경로
- `CACHE_TTL`: 캐시 TTL (초)
- `TIMEZONE_OFFSET`: EST 시간대 오프셋

## 🧪 테스트

### 테스트 실행
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### 주요 테스트
- `tests/test_c1_extraction.py` - C1 날짜 추출 검증
- `tests/test_statistics.py` - 통계 로직 검증 (21개 테스트)

## 📝 코드 수정 시 주의사항

1. **DatetimeIndex 정규화**: 모든 DataFrame은 로드 시점에 정규화되어야 함
2. **C1 날짜**: 패턴 완성 시점이 아닌 다음 봉(C1)을 분석
3. **통계 공식**: Wilson Score, Bonferroni 보정 등 수학적 정의 변경 금지
4. **시간대 변환**: EST/EDT 변환 로직 변경 금지
5. **공통 함수**: `core/indicators.py`의 함수들은 다른 전략에서도 재사용 가능하도록 설계됨

## 🔄 최근 변경사항 (2026-01)

### 하이브리드 전략 라이브 모드 추가
- `analyze_live_mode()` 함수 추가
- 완성된 전 봉 기준으로 계산 (진행 중인 봉 제외)
- 지표 계산 함수를 `core/indicators.py`로 이동 (재사용 가능)

### 코드 정리
- 불필요한 import 제거
- 중복 코드 제거 (`_prepare_indicators_and_signals()` 공통 함수 추가)
- `compute_refined_indicators` → `compute_live_indicators` 통합

## 📚 참고 문서

- **README.md**: 프로젝트 전체 개요
- **ARCHITECTURE.md**: 상세 아키텍처 설명
- **API.md**: API 명세서
- **PROJECT_STRUCTURE.md**: 파일 구조 상세

## 🚀 실행 방법

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API 문서: http://localhost:8000/docs
