"""Market domain schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketCoinPathParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)


class MarketOHLCVPathParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)


class MarketOHLCVQueryParams(BaseModel):
    use_csv: bool = False
    limit: int = Field(default=3000, ge=1, le=10000)
    end_time: Optional[int] = Field(default=None, ge=1)


class MarketPricePayload(BaseModel):
    last: float
    percentage: float
    high: float
    low: float
    volume: float


class MarketPricesEnvelope(BaseModel):
    success: bool
    data: Dict[str, MarketPricePayload]


class FearGreedEnvelope(BaseModel):
    success: bool
    data: Dict[str, Any]


class TimeframesPayload(BaseModel):
    all: List[str]
    binance: List[str]
    csv: List[str]


class TimeframesEnvelope(BaseModel):
    success: bool
    data: TimeframesPayload


class OHLCVRow(BaseModel):
    model_config = ConfigDict(extra="allow")


class OHLCVEnvelope(BaseModel):
    success: bool
    data: List[OHLCVRow]
    source: str
    count: int


__all__ = [
    "FearGreedEnvelope",
    "MarketCoinPathParams",
    "MarketOHLCVPathParams",
    "MarketOHLCVQueryParams",
    "MarketPricesEnvelope",
    "OHLCVEnvelope",
    "TimeframesEnvelope",
]
