"""Request models for API endpoints.

Domain-specific request schemas are moved to backend/modules/*/schemas.py.
This file keeps backward-compatible imports for legacy call sites.
"""

from pydantic import BaseModel

from modules.backtest.schemas import AdvancedBacktestParams, BacktestParams
from modules.market.schemas import (
    MarketCoinPathParams,
    MarketOHLCVPathParams,
    MarketOHLCVQueryParams,
)
from modules.scanner.schemas import PatternScanParams, ScannerParams
from modules.preset.schemas import PresetSaveRequest
from modules.journal.schemas import JournalEntry
from modules.stats.schemas import (
    BBMidParams,
    ComboFilterParams,
    HybridAnalysisParams,
    HybridBacktestParams,
    HybridLiveModeParams,
    TrendIndicatorsParams,
)
from modules.streak.schemas import StreakAnalysisParams


class WeeklyPatternParams(BaseModel):
    coin: str = "ETH"
    interval: str = "1d"
    deep_drop_threshold: float = -0.05
    rsi_threshold: float = 40
    use_csv: bool = False


class WeeklyPatternManualParams(BaseModel):
    """주간 패턴 수동 입력 백테스트 파라미터"""

    coin: str = "ETH"
    monday_open: float
    tuesday_close: float
    wednesday_date: str
    use_csv: bool = False


__all__ = [
    "StreakAnalysisParams",
    "BacktestParams",
    "BBMidParams",
    "ComboFilterParams",
    "TrendIndicatorsParams",
    "HybridAnalysisParams",
    "HybridBacktestParams",
    "HybridLiveModeParams",
    "PresetSaveRequest",
    "AdvancedBacktestParams",
    "PatternScanParams",
    "ScannerParams",
    "MarketCoinPathParams",
    "MarketOHLCVPathParams",
    "MarketOHLCVQueryParams",
    "JournalEntry",
    "WeeklyPatternParams",
    "WeeklyPatternManualParams",
]
