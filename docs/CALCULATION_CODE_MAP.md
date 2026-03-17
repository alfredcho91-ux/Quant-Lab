# 연속 봉 확률 계산 코드 위치 맵

## 📍 메인 파일
**`backend/strategy/streak/`** — `__init__.py`(진입점), `simple_strategy.py`, `complex_strategy.py`, `common.py`, `statistics.py`

---

## 🔢 확률 계산 로직 위치

### 1. **메인 지속 확률 (Continuation Rate)** 
- **위치**: `strategy/streak/simple_strategy.py` (메인 확률·C1/C2)
- **기능**: N연속 후 다음 봉(C1) 지속/반전 확률, C2 예측
- **수정 위치**: `run_simple_analysis()` 내 continuation/reversal 계산

---

### 2. **신뢰구간 & 통계 검정**
- **위치**: `strategy/streak/simple_strategy.py`, `complex_strategy.py` (호출), `statistics.py`·`common.py` (정의)
- **함수**: `wilson_confidence_interval()` → `statistics.py`
- **함수**: `calculate_binomial_pvalue()` → `common.py`

---

### 3. **두 번째 봉(C2) 예측**
- **위치**: `strategy/streak/simple_strategy.py`, `complex_strategy.py`
- **기능**: C1 결과에 따른 C2 예측 확률 (C1 양봉/음봉별 C2 양봉 확률 등)

---

### 4. **구간별 통계 분석 (RSI/Disparity)**
- **위치**: `strategy/streak/common.py` — `analyze_interval_statistics()`
- **호출**: `simple_strategy.py`, `complex_strategy.py` (RSI/Disparity 구간 분석)

---

### 5. **Short Signal 시뮬레이션**
- **위치**: `strategy/streak/complex_strategy.py`
- **기능**: 숏 진입 시뮬레이션 및 승률 계산 (Complex Mode)

---

### 6. **비교 리포트 (nG + 1R 패턴)**
- **위치**: `strategy/streak/simple_strategy.py`, `complex_strategy.py` (Comparative Report 관련)
- **기능**: n양봉+1음봉 패턴과 비교

---

## 🎯 수정 시 주의사항

### 수정 시 참고:
1. **진입점**: `analyze_streak_pattern()` → `strategy/streak/__init__.py` (오케스트레이션만 담당, Context·캐시·모드 분기)
2. **실제 계산**: `strategy/streak/simple_strategy.py`, `complex_strategy.py`, `common.py`, `statistics.py`로 분리됨
3. **Simple/Complex Mode**: `run_simple_analysis` / `run_complex_analysis`로 분기

### 수정하고 싶다면:

**옵션 1: 추가 함수 분리** (이미 `strategy/streak/*`로 분리된 상태. 세분화 시 참고)
```python
# 계산 함수를 더 쪼갤 때 예시
def calculate_continuation_rate(target_cases: pd.DataFrame) -> dict:
    """메인 지속 확률 계산"""
    pass

def calculate_c2_predictions(df: pd.DataFrame, target_cases: pd.DataFrame) -> dict:
    """C2 예측 확률 계산"""
    pass

def calculate_interval_statistics(...):
    """구간별 통계 (이미 함수로 분리됨)"""
    pass
```

**옵션 2: 직접 수정**
- `simple_strategy.py`: 메인 확률 계산, C2 예측 로직
- `complex_strategy.py`: Short Signal, 구간별 통계, Comparative Report 등
- `streak/common.py`, `streak/statistics.py`: Wilson, binomial p-value, 구간별 통계

---

## 📂 관련 파일

### 백엔드
- `backend/strategy/streak/__init__.py` - 메인 진입점 (`analyze_streak_pattern`)
- `backend/strategy/streak/simple_strategy.py`, `complex_strategy.py` - 전략 로직
- `backend/strategy/streak/common.py`, `statistics.py` - 공통·통계
- `backend/modules/streak/router.py` - API 엔드포인트
- `backend/models/request.py` - 요청 모델

### 프론트엔드
- `frontend/src/pages/StreakAnalysisPage.tsx` - UI 표시
- `frontend/src/types/index.ts` - 타입 정의
- `frontend/src/api/client.ts` - API 클라이언트

---

## 🔍 주요 함수 목록

| 함수명 | 위치 | 기능 |
|--------|------|------|
| `analyze_streak_pattern()` | `strategy/streak/__init__.py` | 메인 진입·오케스트레이션 |
| `run_simple_analysis()` | `strategy/streak/simple_strategy.py` | Simple Mode 분석 |
| `run_complex_analysis()` | `strategy/streak/complex_strategy.py` | Complex Mode 분석 |
| `wilson_confidence_interval()` | `strategy/streak/statistics.py` | 신뢰구간 계산 |
| `calculate_binomial_pvalue()` | `strategy/streak/common.py` | 통계 검정 |
| `analyze_interval_statistics()` | `strategy/streak/common.py` | 구간별 통계 |
| `calculate_signal_score()` | `strategy/streak/common.py` | 시그널 점수 |

---

## 💡 현재 구조 (리팩토링 완료)

`analyze_streak_pattern()`는 오케스트레이션만 담당하며, 계산 로직은 아래처럼 분리되어 있습니다:

```
strategy/streak/
├── __init__.py         → analyze_streak_pattern() [메인 진입, 캐시·모드 분기]
├── simple_strategy.py  → run_simple_analysis()
├── complex_strategy.py → run_complex_analysis()
├── common.py           → load_data, prepare_dataframe, 캐싱, analyze_interval_statistics, calculate_signal_score 등
└── statistics.py       → wilson_confidence_interval, 구간별 통계 등
```
