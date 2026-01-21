# 연속 봉 확률 계산 코드 위치 맵

## 📍 메인 파일
**`backend/services/streak_logic.py`** (1741줄)

---

## 🔢 확률 계산 로직 위치

### 1. **메인 지속 확률 (Continuation Rate)** 
```860:865:backend/services/streak_logic.py
# Main analysis: probability of (n+1)th candle (C1) continuing the streak
continuation_count = int((target_cases['target_bit'] == True).sum())
reversal_count = int((target_cases['target_bit'] == False).sum())
continuation_rate = float(continuation_count / total_cases * 100)
reversal_rate = 100 - continuation_rate
```
- **위치**: Line 860-865
- **기능**: N연속 후 다음 봉이 지속될 확률 계산
- **수정 위치**: ⚠️ 여기서 직접 계산 로직 수정

---

### 2. **신뢰구간 & 통계 검정**
```867:871:backend/services/streak_logic.py
# 신뢰구간 계산 - C1 지속 확률
continuation_ci = wilson_confidence_interval(continuation_count, total_cases)

# 통계적 유의성 검정 (H0: 50% vs H1: ≠50%)
c1_pvalue = calculate_binomial_pvalue(continuation_count, total_cases, 0.5)
```
- **위치**: Line 867-871
- **함수**: `wilson_confidence_interval()` (Line 42-86)
- **함수**: `calculate_binomial_pvalue()` (Line 104-118)

---

### 3. **두 번째 봉(C2) 예측**
```877:903:backend/services/streak_logic.py
# Second bar (C2) prediction based on C1 result
df['next_is_green'] = df['is_green'].shift(-1)

c1_green_cases = target_cases[target_cases['is_green'] == True]
c1_red_cases = target_cases[target_cases['is_red'] == True]

# C1이 양봉일 때 C2가 양봉일 확률
if c1_green_count > 0:
    c2_vals = df.loc[c1_green_cases.index, 'next_is_green'].dropna()
    c2_after_c1_green_rate = float(c2_vals.mean() * 100)

# C1이 음봉일 때 C2가 양봉일 확률
if c1_red_count > 0:
    c2_vals = df.loc[c1_red_cases.index, 'next_is_green'].dropna()
    c2_after_c1_red_rate = float(c2_vals.mean() * 100)
```
- **위치**: Line 877-903
- **기능**: C1 결과에 따른 C2 예측 확률

---

### 4. **구간별 통계 분석 (RSI/Disparity)**
```149:210:backend/services/streak_logic.py
def analyze_interval_statistics(
    data_series: pd.Series,
    target_series: pd.Series,
    bins: List[float],
    confidence: float = CONFIDENCE_LEVEL
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
```
- **위치**: Line 149-210
- **호출 위치**: 
  - Line 1180-1200 (Simple Mode RSI 구간)
  - Line 1250-1270 (Simple Mode Disparity 구간)
  - Line 1380-1400 (Complex Mode RSI 구간)
  - Line 1480-1500 (Complex Mode Disparity 구간)

---

### 5. **Short Signal 시뮬레이션**
```1050:1120:backend/services/streak_logic.py
# Short Signal 계산
short_df = target_cases[target_cases['target_bit'] == True].copy()
# ... 진입가 설정 ...
# ... 체결 시뮬레이션 ...
short_win_rate = (short_win_count / len(filled_cases)) * 100
```
- **위치**: Line 1050-1120
- **기능**: 숏 진입 시뮬레이션 및 승률 계산

---

### 6. **비교 리포트 (nG + 1R 패턴)**
```916:958:backend/services/streak_logic.py
# Comparative Report (nG + 1R pattern)
streak_cond = pd.Series([True] * len(df), index=df.index)
for i in range(2, n + 2):
    streak_cond &= (df['is_green'].shift(i) == True)
reversal_pattern_cond = streak_cond & (df['is_green'].shift(1) == False)
```
- **위치**: Line 916-958
- **기능**: n양봉+1음봉 패턴과 비교

---

## 🎯 수정 시 주의사항

### 수정이 어려운 이유:
1. **한 함수에 모든 로직 집중**: `analyze_streak_pattern()` (436줄부터 시작, ~1300줄)
2. **변수 스코프가 복잡**: `target_cases`, `df`, `target_indices` 등이 계속 수정됨
3. **Simple/Complex Mode 분기**: 같은 계산이 두 곳에 중복

### 수정하고 싶다면:

**옵션 1: 함수 분리 리팩토링** (추천)
```python
# 계산 함수들을 별도로 분리
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
- Line 860-865: 메인 확률 계산 수정
- Line 877-903: C2 예측 로직 수정
- Line 1050-1120: Short Signal 로직 수정

---

## 📂 관련 파일

### 백엔드
- `backend/services/streak_logic.py` - 메인 로직
- `backend/routes/streak.py` - API 엔드포인트
- `backend/models/request.py` - 요청 모델

### 프론트엔드
- `frontend/src/pages/StreakAnalysisPage.tsx` - UI 표시
- `frontend/src/types/index.ts` - 타입 정의
- `frontend/src/api/client.ts` - API 클라이언트

---

## 🔍 주요 함수 목록

| 함수명 | 위치 | 기능 |
|--------|------|------|
| `analyze_streak_pattern()` | Line 436 | 메인 분석 함수 (1300줄) |
| `calculate_continuation_rate()` | Line 860 | ⚠️ 인라인 코드 |
| `calculate_c2_predictions()` | Line 877 | ⚠️ 인라인 코드 |
| `wilson_confidence_interval()` | Line 42 | 신뢰구간 계산 |
| `calculate_binomial_pvalue()` | Line 104 | 통계 검정 |
| `analyze_interval_statistics()` | Line 149 | 구간별 통계 |
| `calculate_signal_score()` | Line 370 | 시그널 점수 |

---

## 💡 리팩토링 제안

현재 `analyze_streak_pattern()` 함수가 너무 큽니다. 다음과 같이 분리하는 것을 권장:

```
streak_logic.py
├── analyze_streak_pattern() [메인]
├── calculate_continuation_rate() [새로 분리]
├── calculate_c2_predictions() [새로 분리]
├── calculate_short_signal() [새로 분리]
├── calculate_comparative_report() [새로 분리]
├── analyze_interval_statistics() [이미 분리됨]
└── wilson_confidence_interval() [이미 분리됨]
```
