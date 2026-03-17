"""Market domain schemas."""

from pydantic import BaseModel, Field


class MarketCoinPathParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)


class MarketOHLCVPathParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)


class MarketOHLCVQueryParams(BaseModel):
    use_csv: bool = False
    limit: int = Field(default=3000, ge=1, le=10000)


__all__ = ["MarketCoinPathParams", "MarketOHLCVPathParams", "MarketOHLCVQueryParams"]
