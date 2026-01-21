# 페이지별 백엔드 코드 매핑

각 페이지가 사용하는 백엔드 코드와 라인 수를 정리한 문서입니다.

## 1. 연속 봉패턴 분석 (StreakAnalysisPage)

**API 엔드포인트**: `/api/streak-analysis`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/streak.py` | 40 | API 라우터 (요청 검증 및 파라미터 변환) |
| `backend/strategy/streak/__init__.py` | 111 | 메인 분석 함수 (캐싱 포함) |
| `backend/strategy/streak/simple_strategy.py` | 589 | 심플 모드 분석 로직 |
| `backend/strategy/streak/complex_strategy.py` | 762 | 복합 모드 분석 로직 |
| `backend/strategy/streak/common.py` | 671 | 공통 유틸리티 (데이터 로딩, 통계 함수) |
| `backend/strategy/streak/statistics.py` | 597 | 통계 계산 함수 (Wilson Score, Bonferroni 보정 등) |
| `backend/strategy/context.py` | 116 | 분석 컨텍스트 관리 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |
| `backend/utils/cache.py` | 90 | 캐시 관리 (간접 사용) |

**총 라인 수**: 약 **3,238줄** (직접 사용: 2,886줄)

---

## 2. 주간 패턴 분석 (WeeklyPatternPage)

**API 엔드포인트**: `/api/weekly-pattern`, `/api/weekly-pattern-backtest`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/stats.py` | 400 | API 라우터 (주간 패턴 관련 부분만) |
| `backend/strategy/weekly_pattern/logic.py` | 338 | 주간 패턴 분석 로직 |
| `backend/strategy/weekly_pattern/backtest.py` | 231 | 주간 패턴 백테스트 로직 |
| `backend/strategy/weekly_pattern/statistics.py` | 199 | 통계 계산 함수 |
| `backend/strategy/weekly_pattern/data_processing.py` | 179 | 데이터 처리 함수 |
| `backend/strategy/weekly_pattern/indicators.py` | 124 | 기술적 지표 계산 |
| `backend/strategy/weekly_pattern/validation.py` | 118 | 데이터 검증 |
| `backend/strategy/weekly_pattern/config.py` | 74 | 설정 관리 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **1,912줄** (직접 사용: 1,650줄)

---

## 3. MA 크로스 통계 (MaCrossPage)

**API 엔드포인트**: `/api/ma-cross`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/stats.py` | 400 | API 라우터 (MA Cross 관련 부분만) |
| `backend/strategy/ma_cross/logic.py` | 112 | MA 크로스 통계 계산 로직 |
| `core/indicators.py` | 355 | 이동평균선 계산 (calculate_smas) |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **1,129줄** (직접 사용: 867줄)

---

## 4. 볼밴 중단 터치 통계 (BBMidPage)

**API 엔드포인트**: `/api/bb-mid`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/stats.py` | 400 | API 라우터 (BB Mid 관련 부분만) |
| `backend/strategy/bb_mid/logic.py` | 294 | 볼밴 중단 터치 분석 로직 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **956줄** (직접 사용: 694줄)

---

## 5. 콤보 필터 통계 (ComboFilterPage)

**API 엔드포인트**: `/api/combo-filter`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/stats.py` | 400 | API 라우터 (Combo Filter 관련 부분만) |
| `backend/strategy/combo_filter/logic.py` | 290 | 콤보 필터 분석 로직 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **952줄** (직접 사용: 690줄)

---

## 6. 멀티 타임프레임 스퀴즈 (MultiTFSqueezePage)

**API 엔드포인트**: `/api/multi-tf-squeeze`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/stats.py` | 400 | API 라우터 (Multi-TF Squeeze 관련 부분만) |
| `backend/strategy/squeeze/logic.py` | 199 | 멀티 타임프레임 스퀴즈 분석 로직 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **861줄** (직접 사용: 599줄)

---

## 7. 패턴 통계 (PatternPage)

**API 엔드포인트**: `/api/ohlcv/{coin}/{interval}`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/market.py` | 140 | API 라우터 (OHLCV 엔드포인트) |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 |
| `backend/data_service.py` | 182 | 데이터 서비스 |

**총 라인 수**: 약 **402줄**

**참고**: 이 페이지는 프론트엔드에서 직접 패턴을 감지하므로 백엔드에서 패턴 분석 로직을 사용하지 않습니다.

---

## 8. 패턴 스캐너 (PatternScannerPage)

**API 엔드포인트**: `/api/pattern-scanner`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/scanner.py` | 152 | API 라우터 (패턴 스캐너 엔드포인트) |
| `backend/services/pattern_logic.py` | 240 | 패턴 감지 및 통계 계산 로직 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **654줄** (직접 사용: 392줄)

---

## 9. 전략 스캐너 (StrategyScannerPage)

**API 엔드포인트**: `/api/scanner`

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/scanner.py` | 152 | API 라우터 (전략 스캐너 엔드포인트) |
| `core/strategies.py` | 59 | 전략 정의 (8개 전략) |
| `core/indicators.py` | 355 | 기술적 지표 계산 (prepare_strategy_data) |
| `core/presets.py` | 26 | 프리셋 관리 |
| `backend/utils/data_loader.py` | 80 | 공통 데이터 로딩 (간접 사용) |
| `backend/data_service.py` | 182 | 데이터 서비스 (간접 사용) |

**총 라인 수**: 약 **854줄** (직접 사용: 592줄)

---

## 10. 매매 일지 (JournalPage)

**API 엔드포인트**: `/api/journal` (GET, POST, DELETE)

### 사용되는 백엔드 코드:

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `backend/routes/journal.py` | 110 | API 라우터 (CRUD 엔드포인트) |
| `core/journal.py` | 88 | 매매 일지 비즈니스 로직 (간접 사용 가능) |

**총 라인 수**: 약 **198줄**

---

## 공통으로 사용되는 코드

다음 파일들은 여러 페이지에서 공통으로 사용됩니다:

| 파일 | 라인 수 | 사용 페이지 |
|------|---------|------------|
| `backend/utils/data_loader.py` | 80 | 모든 분석 페이지 |
| `backend/data_service.py` | 182 | 모든 분석 페이지 |
| `backend/utils/cache.py` | 90 | 연속 봉패턴 분석 |
| `backend/utils/decorators.py` | - | 모든 API 엔드포인트 |
| `backend/utils/exceptions.py` | - | 모든 API 엔드포인트 |
| `backend/main.py` | 64 | 전체 애플리케이션 |

---

## 요약 통계

| 페이지 | 직접 사용 라인 수 | 간접 포함 라인 수 | 주요 전략 파일 |
|--------|------------------|------------------|---------------|
| 연속 봉패턴 분석 | 2,886줄 | 3,238줄 | streak/ (2,619줄) |
| 주간 패턴 분석 | 1,650줄 | 1,912줄 | weekly_pattern/ (1,262줄) |
| MA 크로스 통계 | 867줄 | 1,129줄 | ma_cross/logic.py (112줄) |
| 볼밴 중단 터치 | 694줄 | 956줄 | bb_mid/logic.py (294줄) |
| 콤보 필터 | 690줄 | 952줄 | combo_filter/logic.py (290줄) |
| 멀티 타임프레임 스퀴즈 | 599줄 | 861줄 | squeeze/logic.py (199줄) |
| 패턴 통계 | 402줄 | 402줄 | - (프론트엔드 처리) |
| 패턴 스캐너 | 392줄 | 654줄 | pattern_logic.py (240줄) |
| 전략 스캐너 | 592줄 | 854줄 | strategies.py + indicators.py |
| 매매 일지 | 110줄 | 198줄 | journal.py (110줄) |

**전체 백엔드 코드 (backend/strategy, backend/routes, backend/services, core/)**: 약 **10,354줄**

---

## 참고사항

1. **직접 사용 라인 수**: 해당 페이지가 직접 호출하는 API와 전략 파일의 라인 수
2. **간접 포함 라인 수**: 공통 유틸리티(data_loader, data_service 등)를 포함한 총 라인 수
3. **routes/stats.py**: 여러 통계 분석 API가 하나의 파일에 있으므로, 각 페이지는 해당 부분만 사용합니다.
4. **공통 코드**: data_loader.py, data_service.py 등은 모든 분석 페이지에서 공통으로 사용됩니다.
