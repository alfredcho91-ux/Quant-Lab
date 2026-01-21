# backend/main.py
"""
FastAPI Backend for WolGem's Quant Master React Application
Provides REST API endpoints for market data, indicators, backtesting, etc.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import CORS_ORIGINS

# Import routers
from routes.streak import router as streak_router
from routes.market import router as market_router
from routes.backtest import router as backtest_router
from routes.scanner import router as scanner_router
from routes.stats import router as stats_router
from routes.preset import router as preset_router
from routes.support_resistance import router as support_resistance_router
from routes.strategy import router as strategy_router
from routes.journal import router as journal_router
from core.strategies import STRATS

app = FastAPI(
    title="WolGem Quant Master API",
    description="Backend API for crypto trading analysis platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(streak_router)  # /api/streak-analysis
app.include_router(market_router)  # /api/market/*
app.include_router(backtest_router)  # /api/backtest*
app.include_router(scanner_router)  # /api/scanner, /api/pattern-scanner
app.include_router(stats_router)  # /api/ma-cross, /api/bb-mid, /api/combo-filter, /api/multi-tf-squeeze
app.include_router(preset_router)  # /api/presets
app.include_router(support_resistance_router)  # /api/support-resistance
app.include_router(strategy_router)  # /api/strategy-info
app.include_router(journal_router)  # /api/journal


@app.get("/")
async def root():
    return {"message": "WolGem Quant Master API is running!"}


@app.get("/api/strategies")
async def api_strategies():
    """Get list of available strategies"""
    return {"success": True, "data": STRATS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
