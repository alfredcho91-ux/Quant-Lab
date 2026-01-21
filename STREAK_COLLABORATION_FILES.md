# 연속 봉 패턴 분석 협업 파일 목록

다른 AI와 협업하여 연속 봉 패턴 분석 기능을 개발/수정할 때 공유해야 할 파일 목록입니다.

## 📋 필수 파일 목록

### 1. 핵심 전략 로직 (필수)

```
backend/strategy/streak/
├── __init__.py              # 메인 진입점 (analyze_streak_pattern 함수)
├── simple_strategy.py       # 심플 모드 분석 로직 (589줄)
├── complex_strategy.py      # 복합 모드 분석 로직 (762줄)
├── common.py                # 공통 유틸리티 (671줄)
└── statistics.py            # 통계 계산 함수 (597줄)
```

**총 약 2,619줄**

### 2. API 레이어 (필수)

```
backend/routes/
└── streak.py                # API 엔드포인트 (40줄)
```

### 3. 모델 정의 (필수)

```
backend/models/
└── request.py               # StreakAnalysisParams 정의 (필요한 부분만)
```

**필요한 부분**: `StreakAnalysisParams` 클래스만 (8-27줄)

### 4. 공통 유틸리티 (필수)

```
backend/strategy/
└── context.py               # AnalysisContext 클래스 (116줄)
    # 위치: backend/strategy/context.py
    # common.py에서 "from strategy.context import" 형태로 사용

backend/utils/
├── data_loader.py           # 공통 데이터 로딩 (80줄)
├── cache.py                 # 캐시 관리 (90줄)
├── decorators.py            # API 데코레이터 (40줄)
├── error_handler.py         # 에러 처리 (필요한 부분만)
└── response_builder.py      # 응답 빌더 (필요한 부분만)

backend/
└── data_service.py          # 데이터 서비스 (182줄)
```

**중요**: 
- `context.py`는 `backend/strategy/context.py`에 위치 (streak 디렉토리 밖)
- `common.py`는 `backend/strategy/streak/common.py`에 위치 (streak 디렉토리 안)
- `common.py`에서 `from strategy.context import AnalysisContext` 형태로 import

### 5. 설정 파일 (선택)

```
backend/config/
└── settings.py              # CORS 설정 등 (필요한 부분만)
```

---

## 📦 최소 공유 파일 세트 (독립 실행 가능)

다른 AI가 연속 봉 패턴 분석만 독립적으로 개발/테스트할 수 있는 최소 파일 세트:

### 필수 파일 (약 3,800줄)

```
backend/
├── data_service.py                    # 182줄 - 데이터 로딩
├── strategy/
│   ├── context.py                     # 116줄 - 컨텍스트 관리
│   └── streak/
│       ├── __init__.py                 # 111줄 - 메인 진입점
│       ├── simple_strategy.py          # 589줄 - 심플 모드
│       ├── complex_strategy.py         # 762줄 - 복합 모드
│       ├── common.py                   # 671줄 - 공통 유틸리티
│       └── statistics.py              # 597줄 - 통계 함수
└── utils/
    ├── data_loader.py                  # 80줄 - 데이터 로더
    └── cache.py                        # 90줄 - 캐시 관리
```

### API 테스트용 (선택)

```
backend/
├── routes/
│   └── streak.py                       # 40줄 - API 엔드포인트
├── models/
│   └── request.py                     # StreakAnalysisParams 부분만
└── utils/
    ├── decorators.py                  # 40줄 - 데코레이터
    ├── error_handler.py               # 에러 처리
    └── response_builder.py             # 응답 빌더
```

---

## 🎯 협업 시나리오별 파일 공유 가이드

### 시나리오 1: 통계 로직만 수정 (statistics.py)

**공유 파일:**
- `backend/strategy/streak/statistics.py` (597줄)
- `backend/strategy/streak/common.py` (671줄) - 의존성
- `backend/strategy/context.py` (116줄) - 컨텍스트 (common.py에서 import)

**총 약 1,384줄**

**참고**: `context.py`는 `strategy/` 디렉토리 레벨에 있고, `common.py`는 `strategy/streak/` 안에 있습니다.

### 시나리오 2: 심플 모드만 수정 (simple_strategy.py)

**공유 파일:**
- `backend/strategy/streak/simple_strategy.py` (589줄)
- `backend/strategy/streak/common.py` (671줄) - 의존성
- `backend/strategy/streak/statistics.py` (597줄) - 통계 함수
- `backend/strategy/context.py` (116줄) - 컨텍스트 (common.py에서 import)

**총 약 1,973줄**

**참고**: `context.py`는 `strategy/` 디렉토리 레벨에 있고, 나머지는 `strategy/streak/` 안에 있습니다.

### 시나리오 3: 복합 모드만 수정 (complex_strategy.py)

**공유 파일:**
- `backend/strategy/streak/complex_strategy.py` (762줄)
- `backend/strategy/streak/common.py` (671줄) - 의존성
- `backend/strategy/streak/statistics.py` (597줄) - 통계 함수
- `backend/strategy/context.py` (116줄) - 컨텍스트 (common.py에서 import)

**총 약 2,146줄**

**참고**: `context.py`는 `strategy/` 디렉토리 레벨에 있고, 나머지는 `strategy/streak/` 안에 있습니다.

### 시나리오 4: 전체 기능 개발/리팩토링

**공유 파일:**
- `backend/strategy/streak/` 전체 디렉토리 (2,619줄)
  - `__init__.py` (111줄)
  - `simple_strategy.py` (589줄)
  - `complex_strategy.py` (762줄)
  - `common.py` (671줄) - context.py를 import
  - `statistics.py` (597줄)
- `backend/strategy/context.py` (116줄) - streak 디렉토리 밖에 위치
- `backend/utils/data_loader.py` (80줄)
- `backend/utils/cache.py` (90줄)
- `backend/data_service.py` (182줄)
- `backend/routes/streak.py` (40줄) - API 인터페이스 확인용
- `backend/models/request.py` (StreakAnalysisParams 부분) - 인터페이스 확인용

**총 약 3,227줄**

**디렉토리 구조:**
```
backend/strategy/
├── context.py          ← 여기에 위치 (streak 밖)
└── streak/
    ├── __init__.py
    ├── simple_strategy.py
    ├── complex_strategy.py
    ├── common.py        ← 여기에 위치 (streak 안, context.py를 import)
    └── statistics.py
```

---

## 📝 협업 시 주의사항

### 1. 핵심 제약 조건 (절대 변경 금지)

다음 로직은 통계적 정확성을 위해 절대 변경하면 안 됩니다:

- **C1 날짜 추출**: 패턴 완성 시점이 아닌 **다음 봉(C1)**을 분석해야 함
  - 위치: `simple_strategy.py` 236-246줄, `complex_strategy.py` 380-389줄
  
- **Wilson Score Interval**: 공식 변경 금지, $z = 1.96$ 유지
  - 위치: `statistics.py` 또는 `common.py`
  
- **Bonferroni 보정**: 다중 비교 보정 로직 제거 금지
  - 위치: `statistics.py` 또는 `common.py`
  
- **EST 시간대 변환**: UTC → EST/EDT 변환 로직 변경 금지
  - 위치: `common.py` - `calculate_intraday_distribution()`
  
- **DatetimeIndex 정규화**: 모든 DataFrame은 DatetimeIndex를 보유해야 함
  - 위치: `common.py` - `normalize_indices()`

### 2. 인터페이스 유지

- `analyze_streak_pattern()` 함수 시그니처 변경 금지
- `StreakAnalysisParams` 모델 필드 변경 시 `AnalysisContext`도 함께 수정
- 반환 형식 (Dict[str, Any]) 유지

### 3. 의존성 확인

다음 라이브러리가 필요합니다:
```python
pandas
numpy
scipy
pytz
```

### 4. 테스트

수정 후 다음 테스트를 실행하세요:
```bash
cd backend
pytest tests/test_c1_extraction.py -v
```

---

## 🔧 독립 실행 예시

다른 AI가 독립적으로 테스트할 수 있는 최소 예시:

```python
# test_streak.py
from strategy.streak import analyze_streak_pattern

# 테스트 파라미터
params = {
    "coin": "BTC",
    "interval": "1d",
    "n_streak": 6,
    "direction": "green",
    "use_complex_pattern": False,
    "rsi_threshold": 60.0
}

# 분석 실행
result = analyze_streak_pattern(params)
print(result)
```

필요한 파일만 공유하면 이 코드가 동작해야 합니다.

---

## 📊 파일 크기 요약

| 파일 그룹 | 라인 수 | 용도 |
|---------|--------|------|
| 핵심 전략 로직 (streak/) | 2,619줄 | 분석 알고리즘 |
| 공통 유틸리티 | 468줄 | 데이터 로딩, 캐시 등 |
| API 레이어 | 40줄 | 엔드포인트 |
| 모델 정의 | ~20줄 | 파라미터 정의 |
| **총계** | **~3,147줄** | |

---

## 💡 협업 팁

1. **작은 단위로 공유**: 처음에는 특정 함수나 파일만 공유하고, 필요시 확장
2. **컨텍스트 제공**: 각 파일의 역할과 의존성을 명확히 설명
3. **테스트 케이스 공유**: 기대하는 동작을 보여주는 테스트 코드 포함
4. **제약 조건 강조**: 위의 "핵심 제약 조건" 섹션을 반드시 공유

---

## 📌 빠른 참조

**최소 공유 세트 (통계 로직만 수정):**
- `strategy/streak/statistics.py`
- `strategy/streak/common.py`
- `strategy/context.py`

**전체 기능 개발:**
- `strategy/streak/` 전체
- `strategy/context.py`
- `utils/data_loader.py`
- `utils/cache.py`
- `data_service.py`
