"""Strategy info domain schemas."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class StrategyInfoQueryParams(BaseModel):
    lang: str = Field(default="ko", min_length=2, max_length=5)
    rsi_ob: int = Field(default=70, ge=0, le=100)
    sma_main_len: int = Field(default=200, ge=1, le=5000)
    sma1_len: int = Field(default=20, ge=1, le=5000)
    sma2_len: int = Field(default=60, ge=1, le=5000)


class StrategyPayload(BaseModel):
    id: str
    logic: str
    name_en: str
    name_ko: str
    prefix: str


class StrategiesEnvelope(BaseModel):
    success: bool
    data: List[StrategyPayload]


class StrategyInfoPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class StrategyInfoEnvelope(BaseModel):
    success: bool
    data: Dict[str, Any]


__all__ = [
    "StrategiesEnvelope",
    "StrategyInfoEnvelope",
    "StrategyInfoQueryParams",
]
