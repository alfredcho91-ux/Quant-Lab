# 📦 설치 가이드 (Installation Guide)

이 문서는 Quant Master의 상세 설치 방법을 설명합니다.

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

자세한 환경 변수 설명은 이 문서의 위 섹션(환경 변수 예시)을 기준으로 설정하세요.

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

## 새 환경에서 복원하기

새 컴퓨터나 새 환경에서 작업을 이어가기 위한 가이드입니다.

### Git으로 자동 복원되는 파일들

다음 파일들은 Git 저장소에 포함되어 있어 `git clone` 또는 `git pull`로 자동으로 복원됩니다:

- ✅ **모든 소스 코드** (`backend/`, `frontend/src/`, `core/`)
- ✅ **의존성 파일**: `backend/requirements.txt`, `frontend/package.json`
- ✅ **설정 파일**: `backend/config/`, `frontend/vite.config.ts`, `tailwind.config.js`
- ✅ **시작 스크립트**: `start.sh`
- ✅ **문서**: `README.md`, `ARCHITECTURE.md`, `INSTALL.md` 등
- ✅ **Git 설정**: `.gitignore`

### 수동으로 준비해야 하는 파일들

다음 파일들은 `.gitignore`에 포함되어 있어 Git에 저장되지 않습니다:

#### 1. 환경 변수 파일 (선택사항)

**위치**: 프로젝트 루트 또는 `backend/`

**파일명**: `.env`

**내용 예시**:
```env
# CORS 설정 (프론트엔드 도메인 허용)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 디버그 모드 설정
DEBUG_STREAK_ANALYSIS=false

# 데이터 경로 설정
BINANCE_DATA_PATH=./binance_klines

# 캐시 설정
CACHE_TTL=300
CACHE_MAX_SIZE=100

# API 타임아웃 설정
API_TIMEOUT=30

# 타임존 설정
TIMEZONE_OFFSET=-5
```

**참고**: 환경 변수가 없어도 기본값으로 동작합니다. 필요시에만 생성하세요.

#### 2. CSV 데이터 파일 (선택사항, 용량 큼)

**위치**: `binance_klines/`

**용량**: 수백 MB ~ 수 GB (코인 및 기간에 따라 다름)

**복원 방법**:
- **옵션 1**: Git에 포함하지 않고, 필요시 Binance API에서 자동으로 다운로드됨
- **옵션 2**: 백업이 있다면 `binance_klines/` 폴더 전체를 복사

**참고**: CSV 파일이 없어도 API를 통해 실시간 데이터를 가져올 수 있습니다.

#### 3. 가상환경 및 Node 모듈

- `backend/venv/`: `start.sh` 실행 시 자동으로 생성됩니다.
- `frontend/node_modules/`: `start.sh` 실행 시 자동으로 설치됩니다.

### 복원 단계

#### 1단계: Git 저장소 클론

```bash
git clone <저장소_URL>
cd my_quant_V2
```

또는 기존 저장소가 있다면:

```bash
cd my_quant_V2
git pull origin main
```

#### 2단계: 시작 스크립트 실행

```bash
chmod +x start.sh
./start.sh
```

이 스크립트가 자동으로:
- Python 가상환경 생성 (`backend/venv/`)
- Python 패키지 설치 (`pip install -r requirements.txt`)
- Node 모듈 설치 (`npm install`)
- 백엔드 서버 시작 (포트 8000)
- 프론트엔드 서버 시작 (포트 5173)

#### 3단계: 환경 변수 설정 (선택사항)

필요한 경우 `.env` 파일을 생성하세요:

```bash
# backend/.env 또는 프로젝트 루트/.env
cat > .env << EOF
CORS_ORIGINS=http://localhost:5173
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
EOF
```

#### 4단계: CSV 데이터 복원 (선택사항)

백업이 있다면:

```bash
# binance_klines 폴더를 프로젝트 루트에 복사
cp -r /backup/path/binance_klines ./
```

### 필수 파일 체크리스트

새 환경에서 다음 파일들이 있는지 확인하세요:

**백엔드**:
- [ ] `backend/requirements.txt` ✅ (Git에 포함)
- [ ] `backend/main.py` ✅ (Git에 포함)
- [ ] `backend/config/settings.py` ✅ (Git에 포함)
- [ ] `backend/venv/` ⚠️ (자동 생성됨)
- [ ] `backend/.env` ⚠️ (선택사항, 없어도 됨)

**프론트엔드**:
- [ ] `frontend/package.json` ✅ (Git에 포함)
- [ ] `frontend/vite.config.ts` ✅ (Git에 포함)
- [ ] `frontend/node_modules/` ⚠️ (자동 설치됨)

**공통**:
- [ ] `start.sh` ✅ (Git에 포함)
- [ ] `README.md` ✅ (Git에 포함)
- [ ] `binance_klines/` ⚠️ (선택사항, API로 대체 가능)

### 최소 요구사항

**가장 간단한 복원 방법**:
1. Git 저장소만 클론
2. `./start.sh` 실행

이 두 가지만으로도 모든 작업을 이어갈 수 있습니다! (CSV 데이터는 API로 자동 다운로드됨)

## 다음 단계

설치가 완료되면 [README.md](./README.md)의 "주요 기능" 섹션을 참조하여 기능을 사용해보세요.
