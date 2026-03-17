"""Strategy info domain schemas."""

from pydantic import BaseModel, Field


class StrategyInfoQueryParams(BaseModel):
    lang: str = Field(default="ko", min_length=2, max_length=5)
    rsi_ob: int = Field(default=70, ge=0, le=100)
    sma_main_len: int = Field(default=200, ge=1, le=5000)
    sma1_len: int = Field(default=20, ge=1, le=5000)
    sma2_len: int = Field(default=60, ge=1, le=5000)


__all__ = ["StrategyInfoQueryParams"]

