# routes/__init__.py
# 분리된 API 라우터 모듈들

from .streak import router as streak_router
from .market import router as market_router
from .backtest import router as backtest_router
from .scanner import router as scanner_router
from .stats import router as stats_router
from .preset import router as preset_router
from .support_resistance import router as support_resistance_router
from .strategy import router as strategy_router
from .journal import router as journal_router

__all__ = [
    'streak_router',
    'market_router',
    'backtest_router',
    'scanner_router',
    'stats_router',
    'preset_router',
    'support_resistance_router',
    'strategy_router',
    'journal_router',
]
