# backend/main.py
"""
FastAPI Backend for Quant Master React Application
Provides REST API endpoints for market data, indicators, backtesting, etc.
"""

import sys
import os
import time
import logging
import secrets
from pathlib import Path
from typing import Optional

# Add project root to Python path (for importing core modules)
# This ensures core/ can be imported even when running directly with uvicorn
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from config.settings import CORS_ORIGINS

# Import routers
from modules.streak.router import router as streak_router
from modules.market.router import router as market_router
from modules.backtest.router import router as backtest_router
from modules.scanner.router import router as scanner_router
from modules.stats.router import router as stats_router
from modules.preset.router import router as preset_router
from modules.support_resistance.router import router as support_resistance_router
from modules.strategy_info.router import router as strategy_router
from modules.journal.router import router as journal_router
from modules.ai_lab.router import router as ai_lab_router
from modules.indicators.router import router as indicators_router
from core.strategies import STRATS

security = HTTPBasic(auto_error=False)


def verify_credentials(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """Verify HTTP Basic Auth credentials against environment variables."""
    # 로컬 개발 환경(APP_ENV가 production이 아닐 때)에서는 비밀번호 검사를 건너뜁니다.
    if os.getenv("APP_ENV", "development").lower() != "production":
        return "local_dev"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username = os.getenv("DEMO_USERNAME", "demo")
    correct_password = os.getenv("DEMO_PASSWORD", "demo")
    is_username_correct = secrets.compare_digest(credentials.username, correct_username)
    is_password_correct = secrets.compare_digest(credentials.password, correct_password)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


app = FastAPI(
    title="Quant Master API",
    description="Backend API for crypto trading analysis platform",
    version="1.0.0",
    default_response_class=ORJSONResponse,  # orjson 사용으로 JSON 직렬화 성능 향상
    dependencies=[Depends(verify_credentials)],
)

LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()
SLOW_STREAK_REQUEST_MS = float(os.getenv("SLOW_STREAK_REQUEST_MS", "1000"))

uvicorn_error_logger = logging.getLogger("uvicorn.error")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
for _logger in (uvicorn_error_logger, uvicorn_access_logger):
    _logger.setLevel(LOG_LEVEL)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    """Log request timing for observability, focused on streak-analysis latency."""
    start = time.perf_counter()
    path = request.url.path
    method = request.method
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if path == "/api/streak-analysis":
            uvicorn_error_logger.exception(
                "[timing] %s %s failed in %.2fms",
                method,
                path,
                elapsed_ms,
            )
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    if path == "/api/streak-analysis":
        if elapsed_ms >= SLOW_STREAK_REQUEST_MS:
            uvicorn_error_logger.warning(
                "[timing] slow request: %s %s status=%s elapsed_ms=%.2f threshold_ms=%.2f",
                method,
                path,
                response.status_code,
                elapsed_ms,
                SLOW_STREAK_REQUEST_MS,
            )
        else:
            uvicorn_access_logger.info(
                "[timing] %s %s status=%s elapsed_ms=%.2f",
                method,
                path,
                response.status_code,
                elapsed_ms,
            )
    return response

# Include routers
app.include_router(streak_router)  # /api/streak-analysis
app.include_router(market_router)  # /api/market/*
app.include_router(backtest_router)  # /api/backtest*
app.include_router(scanner_router)  # /api/scanner, /api/pattern-scanner
app.include_router(stats_router)  # /api/bb-mid, /api/combo-filter, /api/hybrid-*
app.include_router(preset_router)  # /api/presets
app.include_router(support_resistance_router)  # /api/support-resistance
app.include_router(strategy_router)  # /api/strategy-info
app.include_router(journal_router)  # /api/journal
app.include_router(ai_lab_router)  # /api/ai/research
app.include_router(indicators_router)  # /api/indicators

# Serve frontend static files
frontend_dist = _project_root / "frontend" / "dist"
frontend_dist.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")



@app.get("/api/strategies")
async def api_strategies():
    """Get list of available strategies"""
    return {"success": True, "data": STRATS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
