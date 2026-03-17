"""Pydantic response models for API schema stability."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class StreakFilterStatus(BaseModel):
    """Filter/processing status for streak analysis."""

    status: str
    reason: Optional[str] = None
    total_matches: Optional[int] = None
    quality_results: Optional[int] = None
    filtered_count: Optional[int] = None
    rsi_threshold: Optional[float] = None

    model_config = ConfigDict(extra="allow")


class StreakAnalysisData(BaseModel):
    """Core streak analysis payload returned under envelope.data."""

    success: bool
    total_cases: int
    continuation_rate: Optional[float] = None
    reversal_rate: Optional[float] = None
    continuation_count: int
    reversal_count: int
    c2_after_c1_green_rate: Optional[float] = None
    c2_after_c1_red_rate: Optional[float] = None
    c1_green_count: int
    c1_red_count: int
    comparative_report: Optional[Dict[str, Any]] = None
    avg_body_pct: Optional[float] = None
    mode: Optional[str] = None
    filter_status: Optional[StreakFilterStatus] = None
    coin: Optional[str] = None
    interval: Optional[str] = None
    n_streak: Optional[int] = None
    direction: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class StreakAnalysisEnvelope(BaseModel):
    """Standardized envelope used by /api/streak-analysis."""

    success: bool
    data: Optional[StreakAnalysisData] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class TrendIndicatorsLatest(BaseModel):
    """Latest trend-indicator values.

    Note:
    - Trend Judgment API exposes Slow Stochastic with `slow_stoch_*` only.
    - Stoch RSI is a separate indicator family and uses `stoch_rsi_*`
      in other analysis paths (e.g. quant lab), not in trend judgment payloads.
    """

    close: Optional[float] = None
    rsi: Optional[float] = None
    macd_hist: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    slow_stoch_5k: Optional[float] = None
    slow_stoch_5d: Optional[float] = None
    slow_stoch_10k: Optional[float] = None
    slow_stoch_10d: Optional[float] = None
    slow_stoch_20k: Optional[float] = None
    slow_stoch_20d: Optional[float] = None
    vwap_20: Optional[float] = None
    supertrend: Optional[float] = None
    supertrend_dir: Optional[float] = None

    model_config = ConfigDict(extra="allow")


class TrendSeries(BaseModel):
    """Time-series payload used for chart rendering."""

    t: List[str]
    v: List[float]

    model_config = ConfigDict(extra="allow")


class TrendIndicatorsData(BaseModel):
    """Payload returned under envelope.data for trend indicators."""

    latest: TrendIndicatorsLatest
    series: Dict[str, TrendSeries]
    interval: str
    coin: str

    model_config = ConfigDict(extra="allow")


class TrendIndicatorsEnvelope(BaseModel):
    """Standardized envelope for /api/trend-indicators."""

    success: bool
    data: Optional[TrendIndicatorsData] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")
