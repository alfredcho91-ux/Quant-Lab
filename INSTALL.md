# 📦 설치 가이드 (Installation Guide)

이 문서는 WolGem Quant Master의 상세 설치 방법을 설명합니다.

## 사전 요구사항

- **Node.js** 18 이상
- **Python** 3.9 이상
- **npm** 또는 **yarn**
- **Git** (선택사항)

## 설치 방법

### 방법 1: 통합 스크립트 사용 (권장)

가장 간단한 방법입니다. 백엔드와 프론트엔드를 자동으로 시작합니다.

```bash
# 실행 권한 부여 (최초 1회)
chmod +x start.sh

# 서버 시작
./start.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
- Python 가상환경 생성 및 활성화
- 백엔드 의존성 설치 (`pip install -r requirements.txt`)
- 프론트엔드 의존성 설치 (`npm install`)
- 백엔드 서버 시작 (포트 8000)
- 프론트엔드 서버 시작 (포트 5173)

### 방법 2: 수동 설치 및 실행

#### 백엔드 설치

```bash
cd backend

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작 (자동 리로드 활성화)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 프론트엔드 설치

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

## 접속 확인

설치가 완료되면 다음 URL로 접속할 수 있습니다:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc

## 문제 해결

### 백엔드 관련

**문제**: `ModuleNotFoundError` 또는 import 오류
```bash
# 해결: 가상환경이 활성화되어 있는지 확인
which python  # macOS/Linux
# 출력: .../venv/bin/python 이어야 함

# 가상환경 재활성화
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**문제**: 포트 8000이 이미 사용 중
```bash
# 해결: 다른 포트 사용
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# 또는 기존 프로세스 종료
pkill -f uvicorn
```

### 프론트엔드 관련

**문제**: `npm install` 실패
```bash
# 해결: 캐시 클리어 후 재시도
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**문제**: 포트 5173이 이미 사용 중
```bash
# 해결: Vite는 자동으로 다음 포트(5174)를 사용합니다
# 또는 수동 지정
npm run dev -- --port 3000
```

### 데이터 관련

**문제**: CSV 데이터를 찾을 수 없음
```bash
# 해결: binance_klines 디렉토리 확인
ls binance_klines/
# 데이터가 없으면 API 모드로 사용 (use_csv: false)
```

## 프로덕션 빌드

### 프론트엔드 빌드

```bash
cd frontend
npm run build
```

빌드된 파일은 `frontend/dist/` 폴더에 생성됩니다.

### 백엔드 배포

프로덕션 환경에서는 `--reload` 옵션을 제거하고 프로세스 매니저를 사용하세요:

```bash
# Gunicorn 사용 예시
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 추가 설정

### 환경 변수 설정

`.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다:

**backend/.env**:
```env
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
CACHE_TTL=300
TIMEZONE_OFFSET=-5
```

**frontend/.env**:
```env
VITE_API_URL=http://localhost:8000
```

자세한 환경 변수 설명은 [README.md](./README.md#-환경-변수)를 참조하세요.

## 테스트 실행

프로젝트에 포함된 유닛 테스트를 실행하여 코드의 정확성을 검증할 수 있습니다.

### 사전 요구사항

테스트를 실행하기 전에 pytest가 설치되어 있어야 합니다:

```bash
cd backend
source venv/bin/activate  # 가상환경 활성화
pip install pytest
```

### C1 날짜 추출 검증 테스트

C1 날짜가 항상 패턴 완성 시점의 다음 날짜(T+1)임을 검증하는 테스트입니다.

**테스트 실행:**
```bash
cd backend
source venv/bin/activate  # 가상환경 활성화
pytest tests/test_c1_extraction.py -v
```

**특정 테스트만 실행:**
```bash
# C1이 항상 T+1인지 검증
pytest tests/test_c1_extraction.py::TestC1Extraction::test_c1_is_always_next_candle_simple_mode -v

# 인덱스 범위 체크 검증
pytest tests/test_c1_extraction.py::TestC1Extraction::test_c1_extraction_index_bounds_check -v
```

**테스트 커버리지 확인:**
```bash
pip install pytest-cov
pytest tests/test_c1_extraction.py --cov=strategy --cov-report=html
```

> **중요**: 리팩토링 전/후 반드시 이 테스트가 통과해야 합니다. C1 날짜 추출은 핵심 로직이므로 자동화된 검증이 필수입니다.

## 다음 단계

설치가 완료되면 [README.md](./README.md)의 "주요 기능" 섹션을 참조하여 기능을 사용해보세요.
