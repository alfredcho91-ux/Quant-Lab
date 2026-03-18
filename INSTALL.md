# Installation Guide

This document explains how to install, run, test, and restore Quant-Lab in a clean environment.

## Prerequisites

- Node.js 18+
- Python 3.9+
- `npm` or `yarn`
- Git (recommended)

## Option 1: Start With The Unified Script

This is the fastest path for local setup. It bootstraps both the backend and the frontend.

```bash
# grant execute permission once
chmod +x start.sh

# start backend and frontend
./start.sh
```

The script automatically:

- creates and activates a Python virtual environment
- installs backend dependencies with `pip install -r requirements.txt`
- installs frontend dependencies with `npm install`
- starts the backend on port `8000`
- starts the frontend on port `5173`

## Option 2: Manual Setup

### Backend

```bash
cd backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Windows activation:

```bash
venv\Scripts\activate
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Verify The Services

After startup, these URLs should be available:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Backend

Problem: `ModuleNotFoundError` or import errors

```bash
which python
source venv/bin/activate
pip install -r requirements.txt
```

Problem: port `8000` is already in use

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
pkill -f uvicorn
```

### Frontend

Problem: `npm install` fails

```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

Problem: port `5173` is already in use

```bash
npm run dev -- --port 3000
```

### Data

Problem: CSV data is missing

```bash
ls binance_klines/
```

If no CSV files are present, the app can still run in API mode with `use_csv: false`.

## Production Build

### Frontend

```bash
cd frontend
npm run build
```

The compiled output is written to `frontend/dist/`.

### Backend

For production, remove `--reload` and use a process manager.

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables

You can create `.env` files if you want explicit local overrides.

Backend example:

```env
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
CACHE_TTL=300
TIMEZONE_OFFSET=-5
```

Frontend example:

```env
VITE_API_URL=http://localhost:8000
```

Defaults are sufficient for most local runs, so environment files are optional.

## Running Tests

```bash
cd backend
source venv/bin/activate
pip install pytest
pytest tests/ -v
```

### C1 Extraction Regression Test

This validates that `C1` is always the candle immediately after pattern completion (`T+1`).

```bash
cd backend
source venv/bin/activate
pytest tests/test_c1_extraction.py -v
```

Run a single assertion path:

```bash
pytest tests/test_c1_extraction.py::TestC1Extraction::test_c1_is_always_next_candle_simple_mode -v
pytest tests/test_c1_extraction.py::TestC1Extraction::test_c1_extraction_index_bounds_check -v
```

Coverage example:

```bash
pip install pytest-cov
pytest tests/test_c1_extraction.py --cov=strategy --cov-report=html
```

This regression must stay green before and after refactors because `C1` extraction is a critical analytical invariant.

## Restoring In A New Environment

This section covers what Git restores automatically and what stays local-only.

### Files Restored By Git

- all source code under `backend/`, `frontend/src/`, and `core/`
- dependency manifests such as `backend/requirements.txt` and `frontend/package.json`
- configuration files such as `backend/config/`, `frontend/vite.config.ts`, and `tailwind.config.js`
- startup scripts such as `start.sh`
- repository docs such as `README.md`, `ARCHITECTURE.md`, and `INSTALL.md`
- repo hygiene files such as `.gitignore`

### Files You May Need To Recreate Manually

#### 1. Environment files

- Location: project root or `backend/`
- Filename: `.env`
- Optional: yes

Example:

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
CACHE_TTL=300
CACHE_MAX_SIZE=100
API_TIMEOUT=30
TIMEZONE_OFFSET=-5
```

#### 2. CSV market data

- Location: `binance_klines/`
- Size: hundreds of MB to multiple GB depending on coins and intervals
- Restore options:
  - keep it outside Git and let the app fetch from the Binance API when needed
  - copy a local backup back into `binance_klines/`

#### 3. Local environments and package installs

- `backend/venv/` is created automatically by `start.sh`
- `frontend/node_modules/` is installed automatically by `start.sh`

## Minimal Restore Workflow

```bash
git clone https://github.com/alfredcho91-ux/Quant-Lab.git
cd Quant-Lab
chmod +x start.sh
./start.sh
```

If you already have the repository:

```bash
cd Quant-Lab
git pull origin main
```

Optional environment setup:

```bash
cat > .env << EOF
CORS_ORIGINS=http://localhost:5173
DEBUG_STREAK_ANALYSIS=false
BINANCE_DATA_PATH=./binance_klines
EOF
```

Optional CSV restore:

```bash
cp -r /backup/path/binance_klines ./
```

## Restore Checklist

Backend:

- [ ] `backend/requirements.txt`
- [ ] `backend/main.py`
- [ ] `backend/config/settings.py`
- [ ] `backend/venv/` if you have already bootstrapped locally
- [ ] `backend/.env` if you need overrides

Frontend:

- [ ] `frontend/package.json`
- [ ] `frontend/vite.config.ts`
- [ ] `frontend/node_modules/` if you have already installed locally

Shared:

- [ ] `start.sh`
- [ ] `README.md`
- [ ] `binance_klines/` if you want local CSV caching instead of API-only mode

## Next Step

After installation, start with [README.md](./README.md) for the product overview and feature map.
