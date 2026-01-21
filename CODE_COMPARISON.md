# 연속 음봉 분석 코드 비교

## 제공된 코드 vs 현재 프로젝트 코드

### 1. 패턴 식별 방식

#### 제공된 코드
```python
# 과거 6일의 음봉 합계 계산
df['prev_red_6_sum'] = df['is_red'].shift(1).rolling(window=6).sum()
df['is_after_6_red'] = df['prev_red_6_sum'] == 6
target_days = df[df['is_after_6_red']]
```
- **방식**: `shift(1).rolling(6).sum()` 사용
- **의미**: 과거 6일의 음봉 합계가 6인 지점 = 6연속 음봉이 완성된 **다음 날**

#### 현재 프로젝트 코드
```python
condition = pd.Series([True] * len(df), index=df.index)
for i in range(1, n + 1):
    condition &= (df['target_bit'].shift(i) == True)
target_cases = df[condition]
```
- **방식**: 각 시점에서 과거 N개 봉을 개별적으로 체크
- **의미**: N연속 패턴이 완성된 **시점 자체**를 찾음

### 2. 분석 대상 시점

| 구분 | 제공된 코드 | 현재 프로젝트 |
|------|------------|--------------|
| **대상** | 6연속 음봉 다음 날 (7번째 날) | N연속 패턴 완성 시점 |
| **시각화** | `R R R R R R [7]` | `R R R R R [6] C1` |
| **의미** | "6연속 후 다음 날" | "패턴 완성 시점의 다음 봉(C1)" |

### 3. 결과 해석

#### 제공된 코드
```python
prob_red = (target_days['is_red'].sum() / total_occurrences * 100)
```
- **결과**: "7번째 날이 음봉일 확률"
- **의미**: 6연속 음봉 후에도 계속 음봉일 확률 (연속성 확률)

#### 현재 프로젝트
```python
continuation_rate = (continuation_count / total_cases * 100)
```
- **결과**: "C1이 continuation/reversal인 확률"
- **의미**: 패턴 완성 후 다음 봉이 같은 방향(continuation) 또는 반대 방향(reversal)일 확률

### 4. 코드 구조 비교

#### 제공된 코드
- ✅ 단순하고 직관적
- ✅ 빠른 실행 속도
- ❌ 제한적인 분석 (확률만 계산)
- ❌ 통계적 유의성 검증 없음

#### 현재 프로젝트
- ✅ 포괄적인 분석 (C1/C2, RSI, Disparity 등)
- ✅ 통계적 유의성 검증 (Wilson CI, p-value)
- ✅ NY Trading Guide (시간대별 분석)
- ✅ Comparative Report
- ❌ 복잡한 구조

### 5. 핵심 차이 요약

| 항목 | 제공된 코드 | 현재 프로젝트 |
|------|-----------|--------------|
| **패턴 식별** | `rolling().sum()` | 개별 `shift()` 체크 |
| **분석 시점** | 패턴 완성 **다음 날** | 패턴 완성 **시점** |
| **결과** | 7번째 날 음봉 확률 | C1 continuation/reversal 확률 |
| **통계 검증** | 없음 | Wilson CI, p-value |
| **추가 분석** | 없음 | C2, RSI, Disparity, 시간대별 |

### 6. 실제 동작 예시

#### 제공된 코드
```
데이터: R R R R R R R (7연속 음봉)
        ↑
        이 시점에서 is_after_6_red = True
        → 7번째 날이 음봉인지 확인
```

#### 현재 프로젝트
```
데이터: R R R R R R (6연속 음봉) C1
                    ↑
                    이 시점에서 패턴 완성
                    → C1이 음봉(continuation)인지 양봉(reversal)인지 확인
```

### 7. 결론

**제공된 코드**는 "6연속 음봉 다음 날(7번째)이 음봉일 확률"을 계산하는 **단순 통계 분석**입니다.

**현재 프로젝트**는 "N연속 패턴 완성 시점의 다음 봉(C1)이 continuation/reversal인지"를 분석하는 **종합적인 패턴 분석 시스템**입니다.

두 코드는 **분석 목적과 시점이 다르므로**, 직접 비교하기보다는 각각의 목적에 맞게 사용하는 것이 적절합니다.
