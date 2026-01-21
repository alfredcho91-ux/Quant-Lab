# 🚀 작업 환경 복원 가이드

새 컴퓨터나 새 환경에서 작업을 이어가기 위한 필수 파일 및 설정 가이드입니다.

## ✅ Git으로 자동 복원되는 파일들

다음 파일들은 Git 저장소에 포함되어 있어 `git clone` 또는 `git pull`로 자동으로 복원됩니다:

### 필수 파일 (자동 복원됨)
- ✅ **모든 소스 코드** (`backend/`, `frontend/src/`, `core/`)
- ✅ **의존성 파일**: `backend/requirements.txt`, `frontend/package.json`
- ✅ **설정 파일**: `backend/config/`, `frontend/vite.config.ts`, `tailwind.config.js`
- ✅ **시작 스크립트**: `start.sh`
- ✅ **문서**: `README.md`, `ARCHITECTURE.md`, `INSTALL.md` 등
- ✅ **Git 설정**: `.gitignore`

## ⚠️ 수동으로 준비해야 하는 파일들

다음 파일들은 `.gitignore`에 포함되어 있어 Git에 저장되지 않습니다. 새 환경에서 수동으로 준비해야 합니다:

### 1. 환경 변수 파일 (선택사항)

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

### 2. CSV 데이터 파일 (선택사항, 용량 큼)

**위치**: `binance_klines/`

**용량**: 수백 MB ~ 수 GB (코인 및 기간에 따라 다름)

**내용**: Binance 히스토리컬 데이터 CSV 파일들

**복원 방법**:
- **옵션 1**: Git에 포함하지 않고, 필요시 Binance API에서 자동으로 다운로드됨
- **옵션 2**: 백업이 있다면 `binance_klines/` 폴더 전체를 복사

**참고**: CSV 파일이 없어도 API를 통해 실시간 데이터를 가져올 수 있습니다.

### 3. 가상환경 (자동 생성됨)

**위치**: `backend/venv/`

**복원 방법**: `start.sh` 실행 시 자동으로 생성됩니다.

### 4. Node 모듈 (자동 설치됨)

**위치**: `frontend/node_modules/`

**복원 방법**: `start.sh` 실행 시 자동으로 설치됩니다.

## 📋 새 환경에서 복원하는 단계

### 1단계: Git 저장소 클론

```bash
git clone <저장소_URL>
cd my_quant_V2
```

또는 기존 저장소가 있다면:

```bash
cd my_quant_V2
git pull origin main
```

### 2단계: 시작 스크립트 실행

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

### 3단계: 환경 변수 설정 (선택사항)

필요한 경우 `.env` 파일을 생성하세요:

```bash
# backend/.env 또는 프로젝트 루트/.env
cat > .env << EOF
CORS_ORIGINS=http://localhost:5173
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
EOF
```

### 4단계: CSV 데이터 복원 (선택사항)

백업이 있다면:

```bash
# binance_klines 폴더를 프로젝트 루트에 복사
cp -r /backup/path/binance_klines ./
```

## 🔍 필수 파일 체크리스트

새 환경에서 다음 파일들이 있는지 확인하세요:

### 백엔드
- [ ] `backend/requirements.txt` ✅ (Git에 포함)
- [ ] `backend/main.py` ✅ (Git에 포함)
- [ ] `backend/config/settings.py` ✅ (Git에 포함)
- [ ] `backend/venv/` ⚠️ (자동 생성됨)
- [ ] `backend/.env` ⚠️ (선택사항, 없어도 됨)

### 프론트엔드
- [ ] `frontend/package.json` ✅ (Git에 포함)
- [ ] `frontend/vite.config.ts` ✅ (Git에 포함)
- [ ] `frontend/node_modules/` ⚠️ (자동 설치됨)

### 공통
- [ ] `start.sh` ✅ (Git에 포함)
- [ ] `README.md` ✅ (Git에 포함)
- [ ] `binance_klines/` ⚠️ (선택사항, API로 대체 가능)

## 💾 백업 권장 사항

### 필수 백업 (Git에 포함되지 않음)
1. **환경 변수**: `.env` 파일 (있는 경우)
2. **CSV 데이터**: `binance_klines/` 폴더 (용량이 크지만 필요시)

### 자동 백업됨 (Git에 포함)
- 모든 소스 코드
- 설정 파일
- 의존성 목록

## 🚨 주의사항

1. **`.env` 파일**: 민감한 정보가 포함될 수 있으므로 Git에 커밋하지 마세요 (이미 `.gitignore`에 포함됨)
2. **`binance_klines/`**: 용량이 크므로 Git에 포함하지 않습니다. 필요시 별도 백업하세요.
3. **가상환경**: `venv/`와 `node_modules/`는 자동으로 생성되므로 백업할 필요 없습니다.

## ✅ 최소 요구사항

**가장 간단한 복원 방법**:
1. Git 저장소만 클론
2. `./start.sh` 실행

이 두 가지만으로도 모든 작업을 이어갈 수 있습니다! (CSV 데이터는 API로 자동 다운로드됨)

---

**마지막 업데이트**: 2026-01-20
