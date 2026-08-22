# backend/main.py
"""
FastAPI Backend for Quant Master React Application
Provides REST API endpoints for market data, indicators, backtesting, etc.
"""

import os
import time
import logging
import secrets
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from backend.config.settings import (
    CORS_ORIGINS,
    PROJECT_ROOT,
    get_app_environment,
    get_basic_auth_credentials,
)

# Import routers
from backend.modules.streak.router import router as streak_router
from backend.modules.market.router import router as market_router
from backend.modules.backtest.router import router as backtest_router
from backend.modules.stats.router import router as stats_router
from backend.modules.preset.router import router as preset_router
from backend.modules.support_resistance.router import router as support_resistance_router
from backend.modules.strategy_info.router import router as strategy_router
from backend.modules.journal.router import router as journal_router
from backend.modules.ai_lab.router import router as ai_lab_router
from backend.modules.deepcoin.router import router as deepcoin_router
from backend.modules.indicators.router import router as indicators_router
from backend.utils.log_redaction import install_log_redaction

install_log_redaction()

security = HTTPBasic(auto_error=False)

# Production credentials must be present before the application can accept traffic.
if get_app_environment() == "production":
    get_basic_auth_credentials()


def verify_credentials(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
):
    """Verify HTTP Basic Auth credentials against environment variables."""
    if get_app_environment() != "production":
        client = request.client.host if request.client else ""
        if client in {"127.0.0.1", "::1", "testclient"}:
            return "local_dev"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development mode only accepts loopback requests",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username, correct_password = get_basic_auth_credentials()
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


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    """Do not echo submitted API credentials in validation responses."""
    fields = [
        {
            "location": [str(part) for part in error.get("loc", ())],
            "message": str(error.get("msg", "Invalid value")),
            "type": str(error.get("type", "validation_error")),
        }
        for error in exc.errors()
    ]
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": {"fields": fields},
        },
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
app.include_router(stats_router)  # /api/bb-mid, /api/hybrid-*
app.include_router(preset_router)  # /api/presets
app.include_router(support_resistance_router)  # /api/support-resistance
app.include_router(strategy_router)  # /api/strategy-info
app.include_router(journal_router)  # /api/journal
app.include_router(deepcoin_router)  # /api/deepcoin/*
app.include_router(ai_lab_router)  # /api/ai/research
app.include_router(indicators_router)  # /api/indicators

# Serve frontend static files
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
frontend_dist.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
