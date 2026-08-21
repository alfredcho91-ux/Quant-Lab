"""Stats domain schemas."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class BBMidParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    intervals: List[str] = Field(default_factory=lambda: ["1h", "4h"], min_length=1, max_length=20)
    start_side: Literal["lower", "upper"] = "lower"
    max_bars: int = Field(default=7, ge=1, le=200)
    regime: Optional[str] = None
    use_csv: bool = False


class TrendIndicatorsParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="4h", min_length=2, max_length=4)
    use_csv: bool = False


class HybridAnalysisParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategies: Optional[List[str]] = None


class HybridBacktestParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategy: str = Field(default="SMA_ADX_Strong", min_length=1, max_length=100)
    tp: float = Field(default=2.0, ge=0.0, le=100.0)
    sl: float = Field(default=1.0, ge=0.0, le=100.0)
    max_hold: int = Field(default=5, ge=1, le=500)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_strategy(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if payload.get("strategy") == "EMA_ADX_Strong":
                payload["strategy"] = "SMA_ADX_Strong"
            return payload
        return data


class HybridLiveModeParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategies: Optional[List[str]] = None


class BBMidResultPayload(BaseModel):
    interval: str
    events: int
    success: int
    success_rate: Optional[float] = None
    avg_bars_to_mid: Optional[float] = None
    error: Optional[str] = None


class BBMidEnvelope(BaseModel):
    success: bool
    data: List[BBMidResultPayload]
    excursions: Dict[str, Dict[str, float]]
    start_side: str


class HybridAnalysisEnvelope(BaseModel):
    success: bool
    coin: str
    interval: str
    total_candles: int
    strategies: List[Dict[str, Any]]


class HybridBacktestEnvelope(BaseModel):
    success: bool
    coin: str
    interval: str
    strategy: str
    total_candles: int
    trades: List[Dict[str, Any]]
    summary: Dict[str, Any]
    warnings: Optional[List[str]] = None


class HybridLiveEnvelope(BaseModel):
    success: bool
    coin: str
    interval: str
    timestamp: str
    current_price: Optional[float] = None
    strategies: List[Dict[str, Any]]


__all__ = [
    "BBMidEnvelope",
    "BBMidParams",
    "HybridAnalysisEnvelope",
    "HybridAnalysisParams",
    "HybridBacktestEnvelope",
    "HybridBacktestParams",
    "HybridLiveEnvelope",
    "HybridLiveModeParams",
    "TrendIndicatorsParams",
]
