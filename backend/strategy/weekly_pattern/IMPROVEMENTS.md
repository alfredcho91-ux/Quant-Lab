# 주간패턴 분석 코드 개선사항

## 📋 개선 요약

### 1. 통계적 유의성 검증 추가 ✅
**문제점:**
- 샘플 수가 적어도 결과를 신뢰할 수 있는지 검증이 없음
- 다른 분석(streak analysis)에는 신뢰구간이 있지만 주간패턴에는 없음

**개선사항:**
- `wilson_confidence_interval()` 함수 추가: 소수 샘플에서도 안정적인 신뢰구간 계산
- `calculate_binomial_pvalue()` 함수 추가: 통계적 유의성 검정 (H0: 50% vs H1: ≠50%)
- 각 필터 결과에 신뢰구간, p-value, 유의성 플래그 추가
- 신뢰도 레벨 표시 (high/medium/low)

**사용 예시:**
```python
{
    "win_rate": 65.5,
    "win_rate_ci": {
        "rate": 65.5,
        "ci_lower": 55.2,
        "ci_upper": 74.8,
        "ci_width": 19.6,
        "is_reliable": true,
        "reliability": "high"
    },
    "win_rate_pvalue": 0.023,
    "is_significant": true
}
```

---

### 2. 데이터 품질 검증 강화 ✅
**문제점:**
- 주간 데이터의 완전성 검증이 약함 (월/화/수/일 모두 있는지 확인 부족)
- 데이터 누락 시 경고 없음

**개선사항:**
- `validate_weekly_data_quality()` 함수 추가
- 품질 점수 계산 (완전한 주 / 전체 주)
- 누락된 요일별 통계 제공
- 데이터 품질 이슈 리포트 생성

**사용 예시:**
```python
{
    "data_quality": {
        "is_valid": true,
        "quality_score": 87.5,
        "valid_weeks": 140,
        "total_weeks": 160,
        "issues": [],
        "missing_days": {}
    }
}
```

---

### 3. 성능 최적화 ✅
**문제점:**
- `groupby` 반복문에서 매번 필터링하는 비효율
- 요일별 데이터 추출이 반복적

**개선사항:**
- `extract_weekly_records_vectorized()` 함수로 벡터화 연산
- 요일 리스트를 활용한 효율적인 필터링
- 불필요한 반복 제거

**성능 향상:**
- 기존: O(n * m) where n=주 수, m=요일 수
- 개선: O(n) 선형 시간 복잡도

---

### 4. 추가 통계 지표 ✅
**문제점:**
- 기본 통계만 제공 (승률, 기대수익률, 변동성, Profit Factor)
- 리스크 지표 부족

**개선사항:**
- **Sharpe Ratio**: 위험 대비 수익률
- **최대 낙폭(MDD)**: 최악의 손실 구간
- **연속 손실/수익 통계**: 최대 연속 손실/수익 횟수
- 각 지표에 대한 상세 정보 제공

**사용 예시:**
```python
{
    "sharpe_ratio": 1.25,
    "max_drawdown": {
        "max_drawdown": -15.3,
        "max_drawdown_pct": -15.3
    },
    "max_consecutive_loss": 4,
    "max_consecutive_win": 6
}
```

---

### 5. 코드 구조 개선 ✅
**문제점:**
- `analyze_weekly_pattern()` 함수가 너무 크고 책임이 많음
- 단일 책임 원칙 위반

**개선사항:**
- 함수 분리:
  - `validate_weekly_data_quality()`: 데이터 검증
  - `extract_weekly_records_vectorized()`: 데이터 추출
  - `calculate_enhanced_stats()`: 통계 계산
  - `wilson_confidence_interval()`: 신뢰구간 계산
  - `calculate_sharpe_ratio()`: Sharpe Ratio 계산
  - `calculate_max_drawdown()`: MDD 계산
- 각 함수가 단일 책임을 가지도록 구조화
- 테스트 가능성 향상

---

### 6. 유연한 요일 패턴 설정 ✅
**문제점:**
- 요일이 하드코딩됨 (월, 화, 수, 일)
- 다른 패턴 테스트 불가

**개선사항:**
- `early_days`, `late_days` 파라미터 추가
- 기본값: `[0, 1]` (월, 화), `[2, 6]` (수, 일)
- 사용자 정의 요일 패턴 지원

**사용 예시:**
```python
# 월-화 vs 수-일 (기본)
analyze_weekly_pattern(df, coin, early_days=[0, 1], late_days=[2, 6])

# 월-수 vs 목-일
analyze_weekly_pattern(df, coin, early_days=[0, 2], late_days=[3, 6])
```

---

### 7. 복합 필터 추가 ✅
**문제점:**
- 개별 필터만 제공 (깊은 하락 OR 과매도)
- 복합 조건 테스트 불가

**개선사항:**
- **복합 필터 추가**: 깊은 하락 + 과매도 동시 조건
- 더 엄격한 필터링으로 신뢰도 향상

---

### 8. 에러 처리 강화 ✅
**문제점:**
- 일부 엣지 케이스 처리 부족
- 에러 메시지가 불명확

**개선사항:**
- 데이터 품질 검증 결과를 에러 응답에 포함
- 더 상세한 에러 메시지
- 안전한 float 변환 (`safe_float()` 사용)

---

## 📊 비교표

| 항목 | 기존 버전 | 개선 버전 |
|------|----------|----------|
| 신뢰구간 | ❌ | ✅ |
| p-value | ❌ | ✅ |
| 데이터 품질 검증 | ⚠️ 기본적 | ✅ 강화 |
| Sharpe Ratio | ❌ | ✅ |
| MDD | ❌ | ✅ |
| 연속 손실/수익 | ❌ | ✅ |
| 복합 필터 | ❌ | ✅ |
| 유연한 요일 설정 | ❌ | ✅ |
| 성능 최적화 | ⚠️ | ✅ |

---

## 🚀 사용 방법

### 기존 코드와의 호환성
기존 `logic.py`와 동일한 인터페이스를 유지하므로, 기존 코드를 그대로 사용할 수 있습니다.

### 개선 버전 사용하기
```python
from strategy.weekly_pattern.logic_improved import analyze_weekly_pattern

result = analyze_weekly_pattern(
    df=df,
    coin="BTC",
    deep_drop_threshold=-0.05,
    rsi_threshold=40,
    early_days=[0, 1],  # 월, 화
    late_days=[2, 6]    # 수, 일
)
```

---

## 📈 예상 효과

1. **신뢰도 향상**: 통계적 유의성 검증으로 신뢰할 수 있는 결과만 표시
2. **리스크 관리**: Sharpe Ratio, MDD 등으로 리스크 평가 가능
3. **성능 향상**: 벡터화 연산으로 처리 속도 개선
4. **유연성**: 다양한 요일 패턴 테스트 가능
5. **데이터 품질**: 데이터 문제 조기 발견 및 대응

---

## 🔄 마이그레이션 가이드

### 단계별 마이그레이션

1. **1단계**: 개선 버전 테스트
   ```python
   # 기존 코드는 그대로 유지
   from strategy.weekly_pattern.logic import analyze_weekly_pattern
   
   # 개선 버전 테스트
   from strategy.weekly_pattern.logic_improved import analyze_weekly_pattern as analyze_improved
   ```

2. **2단계**: 프론트엔드 타입 확장
   - `WeeklyPatternStats` 인터페이스에 신뢰구간, p-value 등 추가 필드 정의

3. **3단계**: 점진적 교체
   - 기존 `logic.py`를 `logic_old.py`로 백업
   - `logic_improved.py`를 `logic.py`로 교체

---

## 🧪 테스트 권장사항

1. **단위 테스트**: 각 함수별 테스트 작성
2. **통합 테스트**: 전체 분석 플로우 테스트
3. **성능 테스트**: 대용량 데이터에서 성능 비교
4. **정확도 테스트**: 기존 결과와 비교 검증

---

## 📝 추가 개선 제안

1. **시각화**: 결과를 차트로 표시 (승률 분포, 수익률 분포 등)
2. **백테스팅**: 실제 거래 시뮬레이션 추가
3. **머신러닝**: 패턴 예측 모델 통합
4. **실시간 알림**: 조건 충족 시 알림 기능
5. **다중 코인 비교**: 여러 코인 동시 분석
