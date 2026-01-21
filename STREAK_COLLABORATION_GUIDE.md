# 연속 봉 패턴 분석 협업 가이드

재부팅 후 연속 봉 패턴 분석 페이지를 다른 AI와 협업하기 위한 상세 가이드입니다.

## 🚀 1단계: 프로그램 재시작

### 백엔드 및 프론트엔드 서버 실행

```bash
cd /Users/geunwoocho/my_quant_V2
./start.sh
```

또는 수동으로:

```bash
# 백엔드 실행
cd backend
source venv/bin/activate  # 가상환경이 없으면 python3 -m venv venv 먼저 실행
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# 프론트엔드 실행
cd frontend
npm install  # node_modules가 없으면
npm run dev &
```

**접속 주소:**
- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 📦 2단계: 다른 AI에게 공유할 파일 목록

### 시나리오별 공유 파일 세트

#### 시나리오 A: 통계 로직만 수정 (statistics.py)

**공유할 파일 (약 1,384줄):**
```
backend/strategy/
└── context.py            # 116줄 - 컨텍스트 관리 (streak 밖에 위치)

backend/strategy/streak/
├── statistics.py         # 597줄 - 통계 계산 함수
└── common.py             # 671줄 - 공통 유틸리티 (context.py를 import)
```

**참고**: 
- `context.py`는 `backend/strategy/context.py`에 위치 (streak 디렉토리 밖)
- `common.py`는 `backend/strategy/streak/common.py`에 위치 (streak 디렉토리 안)
- `common.py`에서 `from strategy.context import AnalysisContext` 형태로 import

**필요한 의존성:**
- `pandas`, `numpy`, `scipy`, `pytz`

---

#### 시나리오 B: 심플 모드만 수정 (simple_strategy.py)

**공유할 파일 (약 1,973줄):**
```
backend/strategy/
└── context.py            # 116줄 - 컨텍스트 클래스 (streak 밖에 위치)

backend/strategy/streak/
├── simple_strategy.py    # 589줄 - 심플 모드 로직
├── common.py             # 671줄 - 공통 유틸리티 (context.py를 import)
└── statistics.py         # 597줄 - 통계 함수
```

**참고**: 
- `context.py`는 `backend/strategy/context.py`에 위치 (streak 디렉토리 밖)
- 나머지는 `backend/strategy/streak/` 안에 위치

---

#### 시나리오 C: 복합 모드만 수정 (complex_strategy.py)

**공유할 파일 (약 2,146줄):**
```
backend/strategy/
└── context.py            # 116줄 - 컨텍스트 클래스 (streak 밖에 위치)

backend/strategy/streak/
├── complex_strategy.py   # 762줄 - 복합 모드 로직
├── common.py             # 671줄 - 공통 유틸리티 (context.py를 import)
└── statistics.py         # 597줄 - 통계 함수
```

**참고**: 
- `context.py`는 `backend/strategy/context.py`에 위치 (streak 디렉토리 밖)
- 나머지는 `backend/strategy/streak/` 안에 위치

---

#### 시나리오 D: 전체 기능 개발/리팩토링 (권장)

**공유할 파일 (약 3,227줄):**
```
backend/
├── strategy/streak/
│   ├── __init__.py       # 111줄 - 메인 진입점
│   ├── simple_strategy.py   # 589줄
│   ├── complex_strategy.py  # 762줄
│   ├── common.py            # 671줄
│   └── statistics.py        # 597줄
├── strategy/
│   └── context.py        # 116줄
├── utils/
│   ├── data_loader.py    # 80줄 - 공통 데이터 로딩
│   └── cache.py          # 90줄 - 캐시 관리
├── data_service.py       # 182줄 - 데이터 서비스
├── routes/
│   └── streak.py         # 40줄 - API 인터페이스 확인용
└── models/
    └── request.py        # StreakAnalysisParams 부분만

core/  (필요시 공유)
├── indicators.py         # 기술적 지표 계산 (간접 사용)
└── support_resistance.py # 지지/저항 (간접 사용)
```

---

## 📋 3단계: 공유 시 포함할 필수 정보

### 1. 핵심 제약 조건 (절대 변경 금지)

다음 로직은 통계적 정확성을 위해 절대 변경하면 안 됩니다:

#### ⚠️ C1 날짜 추출 로직
- **위치**: `simple_strategy.py` 236-246줄, `complex_strategy.py` 380-389줄
- **규칙**: 패턴 완성 시점이 아닌 **다음 봉(C1)**을 분석해야 함
- **금지**: `target_cases.index`를 직접 분석하는 것으로 변경 금지

#### ⚠️ Wilson Score Interval 공식
- **위치**: `statistics.py` - `wilson_confidence_interval()`
- **규칙**: $z = 1.96$ (95% 신뢰수준) 유지 필수
- **금지**: 공식 변경, 샘플 수 < 10일 경우 'Low Reliability' 로직 제거 금지

#### ⚠️ Bonferroni 보정
- **위치**: `common.py` - `analyze_interval_statistics()`
- **규칙**: $\alpha_{adjusted} = \frac{\alpha}{n_{comparisons}}$ 적용 필수
- **금지**: 보정 로직 제거 금지

#### ⚠️ EST 시간대 변환
- **위치**: `statistics.py` - `calculate_intraday_distribution()`
- **규칙**: UTC → EST/EDT 변환 로직 변경 금지, pytz 사용 유지
- **금지**: 4시간 구간 인덱스 계산 변경 금지

#### ⚠️ DatetimeIndex 정규화
- **위치**: `common.py` - `normalize_indices()`
- **규칙**: 모든 DataFrame은 DatetimeIndex를 보유해야 함
- **금지**: 인덱스 타입 검증 로직 생략 금지

### 2. API 인터페이스 명세

**요청 파라미터** (`StreakAnalysisParams`):
```python
{
    "coin": "BTC",              # 코인 심볼
    "interval": "1d",           # 타임프레임
    "n_streak": 6,              # 연속 개수 (Simple Mode)
    "direction": "green",       # 'green' 또는 'red'
    "use_complex_pattern": False,  # 복합 패턴 사용 여부
    "complex_pattern": [1,1,1,-1,-1],  # 복합 패턴 (예: 3양-2음)
    "rsi_threshold": 60.0       # RSI 임계값
}
```

**응답 구조**:
```python
{
    "success": True,
    "mode": "simple" | "complex",
    "total_cases": int,
    "continuation_rate": float | null,
    "rsi_by_interval": Dict[str, IntervalProbability],
    "disp_by_interval": Dict[str, IntervalProbability],
    "complex_pattern_analysis": ComplexPatternAnalysis | null,
    ...
}
```

### 3. 의존성

**필수 라이브러리:**
```
pandas>=2.0
numpy>=1.24
scipy>=1.11
pytz>=2023.3
fastapi>=0.109
pydantic>=2.5
```

---

## 🔧 4단계: 다른 AI에게 전달할 메시지 템플릿

```
안녕하세요! 연속 봉 패턴 분석 기능을 협업하고 싶습니다.

[목적]
- [통계 로직 수정 / 심플 모드 수정 / 복합 모드 수정 / 전체 리팩토링] 중 선택

[공유 파일]
- 다음 파일들을 공유합니다: [파일 목록]
- 총 약 [N]줄의 코드입니다.

[핵심 제약 조건]
⚠️ 다음 로직은 절대 변경하면 안 됩니다:
1. C1 날짜 추출: 패턴 완성 시점이 아닌 다음 봉(C1)을 분석해야 함
2. Wilson Score: z = 1.96 유지, 샘플 < 10일 경우 Low Reliability 표시
3. Bonferroni 보정: 다중 비교 보정 로직 제거 금지
4. EST 시간대 변환: UTC → EST/EDT 변환 로직 변경 금지
5. DatetimeIndex 정규화: 모든 DataFrame은 DatetimeIndex 보유 필수

[테스트 방법]
독립 실행 예시:
```python
from strategy.streak import analyze_streak_pattern

params = {
    "coin": "BTC",
    "interval": "1d",
    "n_streak": 6,
    "direction": "green",
    "use_complex_pattern": False,
    "rsi_threshold": 60.0
}

result = analyze_streak_pattern(params)
print(result)
```

[질문/요청사항]
- [구체적인 수정 사항 또는 질문]
```

---

## 📝 5단계: 협업 후 확인사항

### 코드 수정 후 반드시 확인:

- [ ] C1 날짜 추출 로직이 "다음 봉"을 분석하는가?
- [ ] Wilson Score Interval 공식이 변경되지 않았는가? (z = 1.96)
- [ ] Bonferroni 보정이 적용되는가?
- [ ] EST/EDT 시간대 변환이 정확한가?
- [ ] DatetimeIndex 정규화가 수행되는가?
- [ ] 테스트 코드가 통과하는가?

**테스트 실행:**
```bash
cd backend
source venv/bin/activate
pytest tests/test_c1_extraction.py -v
```

---

## 💡 빠른 참조

**최소 공유 세트 (통계 로직만):**
- `strategy/streak/statistics.py`
- `strategy/streak/common.py` (의존성)
- `strategy/context.py` (의존성, streak 디렉토리 밖에 위치)

**전체 기능 개발:**
- `strategy/streak/` 전체 디렉토리
- `strategy/context.py` (streak 디렉토리 밖에 위치)
- `utils/data_loader.py`
- `utils/cache.py`
- `data_service.py`

**API 인터페이스 확인:**
- `routes/streak.py` (40줄)
- `models/request.py` (StreakAnalysisParams 부분만)

---

## 🔍 상세 파일 위치

모든 파일은 다음 경로에 있습니다:
```
/Users/geunwoocho/my_quant_V2/backend/
```

**핵심 전략 로직:**
- `backend/strategy/streak/`

**공통 유틸리티:**
- `backend/utils/`
- `backend/data_service.py`

**API 레이어:**
- `backend/routes/streak.py`
- `backend/models/request.py`

---

이 가이드를 다른 AI에게 공유하면 연속 봉 패턴 분석 기능을 효과적으로 협업할 수 있습니다!
