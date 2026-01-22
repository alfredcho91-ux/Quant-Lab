# 변경 이력 (Changelog)

## [2026-01-21] 프로젝트 구조 개선

### 주요 변경사항

#### 1. 의존성 관리 개선
- **추가**: `backend/__init__.py` 생성
  - 프로젝트 루트 경로를 한 곳에서 통합 관리
  - `sys.path.insert` 중앙화
- **제거**: 모든 파일에서 개별 `sys.path.insert` 제거 (19개 파일)
  - `routes/`: 5개 파일
  - `strategy/`: 8개 파일
  - `services/`: 1개 파일
  - `tests/`: 2개 파일 (테스트 환경 특성상 유지)
- **효과**: 
  - 코드 가독성 향상
  - 경로 설정 일관성 확보
  - 테스트 환경 안정성 향상

#### 2. 데이터 서비스 구조 개선
- **이동**: `backend/data_service.py` → `backend/utils/data_service.py`
- **수정**: 모든 import 경로 업데이트 (7개 파일)
  - `utils/data_loader.py`
  - `routes/market.py`
  - `routes/support_resistance.py`
  - `strategy/streak/common.py`
  - `strategy/weekly_pattern/logic.py`
  - `strategy/streak/statistics.py`
- **수정**: `BASE_DIR` 경로 수정 (`parent.parent` → `parent.parent.parent`)
- **효과**: 
  - 의존성 역전 문제 해결
  - 모든 데이터 관련 유틸리티가 `utils/`에 집중
  - 구조적 명확성 향상

#### 3. 중복 코드 제거
- **삭제**: `backend/services/squeeze_service.py` (195줄)
- **이유**: `backend/strategy/squeeze/logic.py`와 중복 로직
- **효과**: 
  - 유지보수 비용 감소
  - 버그 수정 일관성 확보
  - 코드 줄수 감소 (~195줄)

#### 4. 명명 개선
- **리네임**: `backend/services/backtest_logic.py` → `backend/services/statistics.py`
- **이유**: 실제로는 통계 계산만 수행 (백테스트 실행이 아님)
- **효과**: 
  - 파일 역할이 더 명확해짐
  - 코드 가독성 향상

### 통계

- **코드 줄수 감소**: 약 388줄 (398줄 삭제 - 10줄 추가)
- **파일 이동**: 1개 (`data_service.py`)
- **파일 삭제**: 1개 (`squeeze_service.py`)
- **파일 리네임**: 1개 (`backtest_logic.py` → `statistics.py`)
- **Import 경로 수정**: 7개 파일
- **sys.path 제거**: 19개 파일

### 문서 업데이트

- `PROJECT_STRUCTURE.md`: 파일 구조 및 최근 변경사항 업데이트
- `ARCHITECTURE.md`: 모듈 설명 및 의존성 관계 업데이트
- `README.md`: 파일 구조 다이어그램 업데이트
- `CHANGELOG.md`: 변경 이력 문서 생성

### 테스트 결과

- ✅ 백엔드 서버 정상 시작
- ✅ 프론트엔드 서버 정상 시작
- ✅ 모든 API 엔드포인트 정상 작동
- ✅ Import 경로 모두 정상
- ✅ BASE_DIR 경로 정상

---

## 이전 변경사항

### 2025년 변경사항
- 주간 패턴 분석 리팩토링
- 통합 필터 테스트 수정
- 타입 및 API 클라이언트 모듈화
- 캐싱 및 컨텍스트 관리
