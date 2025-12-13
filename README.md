# 💎 월젬의 퀀트 마스터 (WolGem's Quant Master)

암호화폐 트레이딩을 위한 8개 전략 백테스트 및 분석 플랫폼입니다.

![License](https://img.shields.io/badge/license-MIT-green)
![React](https://img.shields.io/badge/React-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)

## 📖 개요

React + FastAPI 기반의 암호화폐 트레이딩 분석 플랫폼입니다.
빠른 UI 응답성과 향상된 사용자 경험을 제공합니다.

## ✨ 주요 기능

### 🚀 백테스트 (Backtest)
- **8개 전략 지원**:
  - A1. Connors (RSI2 역추세)
  - A2. Squeeze (변동성 폭발)
  - A3. Turtle (Donchian 추세)
  - A4. Mean Reversion (BB+RSI)
  - B1. RSI Reversal (표준)
  - B2. MA Cross (MA1↔MA2↔MA3)
  - B3. BB Breakout (돌파)
  - B4. Engulfing (장악형)

- **파라미터 커스터마이징**:
  - TP/SL 설정
  - 레버리지 (1x ~ 50x)
  - RSI, EMA, MA, ADX 등 지표 파라미터
  - 볼린저 밴드, ATR, Keltner Channel 설정

- **결과 분석**:
  - 승률, 누적 수익률, 청산 횟수
  - 장세별 성과 분석 (Bull/Bear/Sideways)
  - 거래 내역 테이블 및 CSV 내보내기

### 📈 패턴/캔들 통계
- 캔들스틱 패턴 탐지 (Engulfing, Doji, Hammer 등)
- 패턴별 수익률 통계
- 다양한 타임프레임 지원

### 📊 전략 스캐너
- 실시간 8개 전략 시그널 모니터링
- 자동 새로고침 (1분 간격)
- Long/Short 시그널 표시

### 🌐 시장 정보
- 실시간 가격 표시 (BTC, ETH, SOL, XRP)
- Fear & Greed Index
- 다국어 지원 (한국어/English)

## 🏗️ 프로젝트 구조

```
my_quant_V2/
├── backend/                 # FastAPI 백엔드
│   ├── main.py             # API 엔드포인트
│   ├── data_service.py     # 데이터 서비스
│   └── requirements.txt    # Python 의존성
│
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── api/           # API 클라이언트
│   │   ├── components/    # React 컴포넌트
│   │   │   ├── Chart.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ParamsPanel.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── StrategyExplainer.tsx
│   │   │   └── TradesTable.tsx
│   │   ├── pages/         # 페이지 컴포넌트
│   │   │   ├── BacktestPage.tsx
│   │   │   ├── PatternPage.tsx
│   │   │   └── ScannerPage.tsx
│   │   ├── store/         # 상태 관리 (Zustand)
│   │   ├── types/         # TypeScript 타입
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── core/                    # 핵심 비즈니스 로직
│   ├── indicators.py       # 기술적 지표 계산
│   ├── backtest.py         # 백테스트 엔진
│   ├── strategies.py       # 전략 정의
│   ├── support_resistance.py # 지지/저항 계산
│   └── ...
│
├── binance_klines/          # 히스토리컬 데이터 (CSV)
│
├── start.sh                 # 개발 서버 시작 스크립트
└── README.md
```

## 🛠️ 기술 스택

### Frontend
- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링
- **Zustand** - 상태 관리
- **React Query** - 서버 상태 관리
- **Plotly.js** - 차트 라이브러리
- **React Router** - 라우팅
- **Axios** - HTTP 클라이언트

### Backend
- **FastAPI** - Python 웹 프레임워크
- **CCXT** - 암호화폐 거래소 API
- **Pandas/NumPy** - 데이터 처리
- **Uvicorn** - ASGI 서버

## 🚀 시작하기

### 사전 요구사항
- **Node.js** 18+ 
- **Python** 3.10+
- **npm** 또는 **yarn**

### 설치 및 실행

#### 방법 1: 통합 스크립트 사용 (권장)

```bash
# 실행 권한 부여 (최초 1회)
chmod +x start.sh

# 서버 시작
./start.sh
```

#### 방법 2: 수동 실행

**백엔드 시작:**
```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**프론트엔드 시작:**
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

### 접속
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 📡 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/market/prices` | 시장 가격 조회 |
| GET | `/api/market/fear-greed` | Fear & Greed Index |
| GET | `/api/timeframes/{coin}` | 사용 가능한 타임프레임 |
| GET | `/api/strategies` | 전략 목록 |
| GET | `/api/strategy-info/{id}` | 전략 설명 |
| GET | `/api/ohlcv/{coin}/{interval}` | OHLCV 데이터 |
| POST | `/api/backtest` | 백테스트 실행 |
| GET | `/api/support-resistance/{coin}/{interval}` | 지지/저항 레벨 |
| GET | `/api/presets` | 프리셋 목록 |
| POST | `/api/presets` | 프리셋 저장 |

## 🎨 UI 특징

- **다크 테마**: 트레이딩에 최적화된 어두운 색상 테마
- **반응형 디자인**: 데스크톱 및 태블릿 지원
- **애니메이션**: 부드러운 전환 효과
- **인터랙티브 차트**: 확대/축소, 드래그 지원

## 📦 배포

### 프로덕션 빌드

```bash
cd frontend
npm run build
```

빌드된 파일은 `dist/` 폴더에 생성됩니다.

### Docker 배포 (선택사항)

```dockerfile
# Dockerfile 예시
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN pip install -r backend/requirements.txt
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx 설정 예시

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 🔧 환경 변수

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

### Backend (.env)
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 📝 기능 체크리스트
- [x] 백테스트 기능
- [x] 8개 전략
- [x] 실시간 시세
- [x] Fear & Greed Index
- [x] 차트 시각화
- [x] 패턴 분석
- [x] 전략 스캐너
- [ ] μ 기반 전략 연구 (추후 추가 예정)
- [ ] 매매 일지 (추후 추가 예정)

## 🤝 기여

버그 리포트, 기능 제안, PR을 환영합니다!

## 📄 라이선스

MIT License

---

**💎 월젬의 퀀트 마스터** - 트레이딩 분석의 새로운 기준

