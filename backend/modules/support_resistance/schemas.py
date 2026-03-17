"""Support resistance domain schemas."""

from pydantic import BaseModel, Field


class SupportResistancePathParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="4h", min_length=2, max_length=4)


class SupportResistanceQueryParams(BaseModel):
    lookback: int = Field(default=3, ge=1, le=200)
    tolerance_pct: float = Field(default=0.3, ge=0.0, le=10.0)
    min_touches: int = Field(default=3, ge=1, le=50)
    show_pivots: bool = False
    htf_option: str = "none"


__all__ = ["SupportResistancePathParams", "SupportResistanceQueryParams"]

