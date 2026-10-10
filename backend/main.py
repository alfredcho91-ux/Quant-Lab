# backend/main.py
"""
FastAPI Backend for Quant Master React Application
Provides REST API endpoints for market data, indicators, backtesting, etc.
"""

import os
import time
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from backend.config.settings import (
    CORS_ORIGINS,
    FRONTEND_DIST_DIR,
    IS_FROZEN,
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
from backend.modules.plan_lab.router import router as plan_lab_router
from backend.utils.log_redaction import install_log_redaction
from backend.config.sample_policy import IS_SAMPLE, install_offline_boundary
from backend.modules.analytics.router import router as analytics_router
from backend.modules.review.router import router as review_router
from backend.modules.experiments.router import router as experiments_router
from backend.modules.experiments.repository import initialize_schema as initialize_experiment_schema
from backend.modules.exchanges.router import router as exchanges_router
from backend.modules.rule_engine.router import router as rule_engine_router
from backend.modules.strategies.router import router as strategies_router
from backend.modules.strategy_assignments.router import router as strategy_assignments_router
from backend.modules.strategy_assignments.repository import initialize_schema as initialize_assignment_schema
from backend.modules.sample.workspace import router as workspace_router, sample_process
from backend.utils.local_request_security import LocalRequestSecurityMiddleware
from backend.utils.frontend_static import FrontendStaticFiles

install_log_redaction()

security = HTTPBasic(auto_error=False)

# Production credentials must be present before the application can accept traffic.
if get_app_environment() == "production":
    get_basic_auth_credentials()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if IS_SAMPLE:
        install_offline_boundary()
        from backend.modules.sample.fixture import build_fixture
        build_fixture()
    initialize_assignment_schema()
    initialize_experiment_schema()
    try:
        yield
    finally:
        sample_process.close()


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
    lifespan=lifespan,
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
app.add_middleware(LocalRequestSecurityMiddleware)


@app.middleware("http")
async def sample_exchange_boundary(request: Request, call_next):
    journal_api = ("/api/health", "/api/desktop/", "/api/workspace", "/api/journal", "/api/plans", "/api/plan-lab", "/api/playbook/", "/api/rule-engine/", "/api/analytics/", "/api/review/", "/api/experiments", "/api/exchanges", "/api/deepcoin", "/api/indicators/")
    if IS_SAMPLE and request.url.path.startswith("/api/") and not request.url.path.startswith(journal_api):
        return ORJSONResponse(status_code=403, content={"success": False, "error": "Quant research tools are unavailable in the journal sample workspace", "error_code": "SAMPLE_OFFLINE"})
    if IS_SAMPLE and request.url.path.startswith(("/api/exchanges", "/api/deepcoin")) and request.method != "GET":
        return ORJSONResponse(status_code=403, content={"success": False, "error": "Exchange connections and sync are disabled in the sample workspace", "error_code": "SAMPLE_OFFLINE"})
    return await call_next(request)


@app.get("/api/health", dependencies=[])
def health():
    return {"success": True, "data": {"service": "quant-lab"}}


@app.post("/api/desktop/shutdown", dependencies=[])
def desktop_shutdown(request: Request):
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="Local requests only")
    server = getattr(request.app.state, "desktop_server", None)
    if server is None:
        raise HTTPException(status_code=409, detail="Desktop shutdown is unavailable")
    server.should_exit = True
    return {"success": True, "data": {"shutting_down": True}}


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
app.include_router(plan_lab_router)  # /api/plans and /api/plan-lab
app.include_router(workspace_router)
app.include_router(strategies_router)
app.include_router(strategy_assignments_router)
app.include_router(rule_engine_router)
app.include_router(analytics_router)
app.include_router(review_router)
app.include_router(experiments_router)
app.include_router(exchanges_router)

# Serve frontend static files
if not FRONTEND_DIST_DIR.exists() and not IS_FROZEN:
    FRONTEND_DIST_DIR.mkdir(parents=True, exist_ok=True)
if not FRONTEND_DIST_DIR.is_dir():
    raise RuntimeError("Quant Lab frontend files are missing from this installation.")
app.mount("/", FrontendStaticFiles(directory=str(FRONTEND_DIST_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
