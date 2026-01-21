# 7번째 봉 확률 계산 차이 분석

## 문제 발견

### 제공된 코드
```python
df['prev_red_6_sum'] = df['is_red'].shift(1).rolling(window=6).sum()
df['is_after_6_red'] = df['prev_red_6_sum'] == 6
target_days = df[df['is_after_6_red']]
prob_red = target_days['is_red'].sum() / len(target_days) * 100
```
- **의미**: "과거 6일이 모두 음봉인 다음 날"을 찾아서, 그 날(7번째 봉)이 음봉인지 확인
- **타겟**: 인덱스 6, 7 (7번째 봉 자체)

### 현재 프로젝트 코드
```python
condition = pd.Series([True] * len(df), index=df.index)
for i in range(1, n + 1):
    condition &= (df['target_bit'].shift(i) == True)
target_cases = df[condition]
df['next_is_green'] = df['is_green'].shift(-1)
c1_red_mask = df.loc[target_cases.index, 'next_is_red'] == True
```
- **의미**: "과거 6일이 모두 음봉인 시점"을 찾아서, 그 다음 봉(C1)이 음봉인지 확인
- **타겟**: 인덱스 6, 7 (6번째 봉 완성 시점, 다음 봉 C1 확인)

## 차이점

| 구분 | 제공된 코드 | 현재 프로젝트 |
|------|-----------|--------------|
| **패턴 식별** | `shift(1).rolling(6).sum() == 6` | `shift(1) & shift(2) & ... & shift(6)` |
| **타겟 의미** | "6연속 음봉 다음 날" (7번째 봉) | "6연속 음봉 완성 시점" (6번째 봉) |
| **분석 대상** | 타겟 인덱스 자체 | 타겟 인덱스의 다음 봉(C1) |
| **결과** | 7번째 봉이 음봉일 확률 | C1이 음봉일 확률 |

## 테스트 결과

```
인덱스:  0   1   2   3   4   5   6   7   8
봉:      R   R   R   R   R   R   R   G   R
```

**제공된 코드**:
- 인덱스 6: 타겟 (7번째 봉 = R) ✅
- 인덱스 7: 타겟 (7번째 봉 = G) ❌
- 확률: 50% (1/2)

**현재 프로젝트**:
- 인덱스 6: 타겟 (C1 = 인덱스 7 = G) ❌
- 인덱스 7: 타겟 (C1 = 인덱스 8 = R) ✅
- 확률: 50% (1/2)

하지만 **분석 대상이 다름**:
- 제공된 코드: 인덱스 6, 7 자체가 7번째 봉
- 현재 프로젝트: 인덱스 6, 7의 다음 봉이 7번째 봉

## 해결 방안

현재 프로젝트 코드를 제공된 코드와 동일하게 동작하도록 수정해야 합니다.

### 옵션 1: 패턴 매칭 방식 변경
```python
# 현재 방식
condition = pd.Series([True] * len(df), index=df.index)
for i in range(1, n + 1):
    condition &= (df['target_bit'].shift(i) == True)

# 변경 후 (제공된 코드 방식)
df['prev_streak_sum'] = df['target_bit'].shift(1).rolling(window=n).sum()
condition = df['prev_streak_sum'] == n
```

### 옵션 2: 타겟 인덱스 자체를 분석 대상으로 사용
```python
# 현재: 다음 봉(C1) 분석
df['next_is_green'] = df['is_green'].shift(-1)
c1_red_mask = df.loc[target_cases.index, 'next_is_red'] == True

# 변경 후: 타겟 인덱스 자체 분석
c1_red_mask = df.loc[target_cases.index, 'is_red'] == True  # direction == "red"인 경우
```

## 권장 사항

**옵션 2를 권장합니다**. 이유:
1. 기존 패턴 매칭 로직을 유지할 수 있음
2. 단순히 분석 대상을 변경하면 됨
3. 다른 부분(C2 분석 등)에 영향을 최소화

하지만 사용자가 "7번째 봉"이라고 명시했으므로, 제공된 코드 방식이 더 정확합니다.
