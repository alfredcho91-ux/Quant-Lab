# 설치 및 운영 가이드

## 요구사항

- Python 3.9 이상
- Node.js 18 이상
- `npm`
- 선택 사항: `binance_klines/`의 로컬 CSV 데이터

## 처음 실행

```bash
chmod +x bootstrap.sh dev.sh start.sh
./start.sh
```

`start.sh`는 `backend/venv` 또는 `frontend/node_modules`가 없을 때만 `bootstrap.sh`를 실행하고 `dev.sh`로 넘깁니다.

- `bootstrap.sh`: Python virtualenv 생성, `backend/requirements.txt` 설치, 프런트 의존성 설치
- `dev.sh`: 백엔드 `8000`, 프런트 `5173` 개발 서버를 함께 실행
- `start.sh`: 위 두 단계를 연결하는 일상용 진입점

강제로 프런트 의존성을 다시 설치하려면 다음을 사용합니다.

```bash
./bootstrap.sh --force
```

## 개별 실행

### Backend

```bash
./bootstrap.sh
backend/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

접속 주소:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- OpenAPI/Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 데이터 소스

기본적으로 Binance Spot REST API를 사용합니다. API 모드에서는 인터넷 연결이 필요합니다. 화면에서 CSV를 선택하면 `binance_klines/`의 아래 형식 파일을 사용합니다.

```text
binance_klines/{COIN}USDT-{interval}-merged.csv
```

예: `BTCUSDT-4h-merged.csv`. 월봉만 파일명에서 `1M` 대신 `1mo`를 사용합니다.

## 환경 변수

대부분의 로컬 실행에는 환경 변수가 필요 없습니다.

| 변수 | 기본값 | 용도 |
| --- | --- | --- |
| `APP_ENV` | `development` | `production`일 때 Basic Auth 활성화 |
| `DEMO_USERNAME` | 없음 | production Basic Auth 사용자명 |
| `DEMO_PASSWORD` | 없음 | production Basic Auth 비밀번호 |
| `CORS_ORIGINS` | localhost 5173, 3000 | 쉼표 구분 CORS 허용 원본 |
| `ANALYSIS_TIMEZONE` | `America/New_York` | 연속봉 시간 분포 분석 시간대 |
| `DATA_CACHE_BACKEND` | `disk` | `memory`, `off` 등으로 디스크 캐시 비활성화 |
| `MEMORY_CACHE_MAX_ITEMS` | `5000` | 메모리 fallback 캐시 상한 |
| `JOURNAL_DIR` | `<project>/journal` | 저널 파일 디렉터리 |
| `JOURNAL_DB_PATH` | `<journal>/trade_journal.db` | 저널 SQLite 경로 |
| `JOURNAL_CSV_PATH` | `<journal>/trade_journal.csv` | 저널 CSV 경로 |
| `DEEPCOIN_API_KEY` | 없음 | Deepcoin 읽기 전용 API 키 |
| `DEEPCOIN_SECRET_KEY` | 없음 | Deepcoin API secret. 서버 환경에서만 읽음 |
| `DEEPCOIN_PASSPHRASE` | 없음 | Deepcoin API passphrase. 서버 환경에서만 읽음 |
| `DEEPCOIN_API_BASE_URL` | `https://api.deepcoin.com` | Deepcoin REST base URL |
| `PRESET_DIR` | `<project>/data` | 프리셋 디렉터리 |
| `PRESETS_FILE` | `<project>/data/presets.json` | 프리셋 파일 경로 |
| `GEMINI_API_KEY` | 없음 | AI Lab 서버 기본 키 |
| `APP_LOG_LEVEL` | `INFO` | Uvicorn 로그 레벨 |
| `SLOW_STREAK_REQUEST_MS` | `1000` | 연속봉 요청 지연 경고 임계값 |

production에서는 `APP_ENV=production`, `DEMO_USERNAME`, `DEMO_PASSWORD`를 함께 설정해야 서버가 시작됩니다.

## Deepcoin 체결 동기화

매매 일지의 Deepcoin 동기화는 읽기 전용 체결·종료 포지션 API만 사용합니다. API 키와 secret, passphrase는 `.env` 또는 운영 환경 변수에만 두며 프런트엔드와 SQLite 저널에는 저장하지 않습니다. `./dev.sh`와 `./start.sh`는 프로젝트 루트의 `.env`를 자동으로 불러옵니다.

```bash
export DEEPCOIN_API_KEY="..."
export DEEPCOIN_SECRET_KEY="..."
export DEEPCOIN_PASSPHRASE="..."
```

처음 설정할 때는 `.env.example`을 참고합니다. `.env`는 Git 추적에서 제외됩니다.

키에는 조회 권한만 설정하고 거래·출금 권한을 해제합니다. Deepcoin API 키의 IP 허용 목록도 설정합니다. 동기화한 체결마다 Binance Spot의 마지막 확정봉에서 RSI, MACD, 3 Slow Stochastic, Stoch RSI, VPVR를 계산해 SQLite JSON 스냅샷으로 보관합니다.

## 검증

```bash
python3 scripts/check_core_imports.py
python3 scripts/check_route_imports.py
backend/venv/bin/python -m pytest -q backend/tests
cd frontend && npm test
cd frontend && npm run lint
cd frontend && npm run build
```

특정 테스트 예시:

```bash
backend/venv/bin/python -m pytest -q backend/tests/test_stats_service_trend.py
backend/venv/bin/python -m pytest -q backend/tests/test_vpvr.py
cd frontend && npm test -- ohlcv
```

## 자주 보는 문제

### 8000 또는 5173 포트가 이미 사용 중인 경우

다른 포트로 직접 실행합니다.

```bash
backend/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
cd frontend && npm run dev -- --port 5174
```

### Binance 요청이 실패하거나 화면이 느린 경우

- 인터넷 연결과 Binance API 접근 가능 여부를 확인합니다.
- 추세판단은 같은 코인/시간대 요청을 프런트와 백엔드에서 TTL 캐시합니다. 수동 새로고침은 필요할 때만 사용합니다.
- CSV가 있다면 화면의 CSV 모드로 전환해 네트워크 의존성을 줄일 수 있습니다.
- `DATA_CACHE_BACKEND=memory`는 디스크 권한 문제를 우회할 수 있지만 서버 재시작 시 캐시가 사라집니다.

### 프런트 의존성이 깨진 경우

```bash
./bootstrap.sh --force
```

### production 배포 전 확인

- `APP_ENV=production`과 Basic Auth 자격 증명을 설정합니다.
- `npm run build` 후 FastAPI가 `frontend/dist`를 정적으로 제공합니다.
- 개발용 `--reload` 없이 process manager나 컨테이너로 실행합니다.
- AI Lab의 Python 실행 엔드포인트는 외부 노출 전에 별도 격리하거나 비활성화합니다.
