"""Scanner domain schemas."""

from typing import List, Literal

from pydantic import BaseModel, Field


class PatternScanParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    intervals: List[str] = Field(default_factory=lambda: ["1h", "4h"], min_length=1, max_length=20)
    tp_pct: float = Field(default=1.0, gt=0.0, le=100.0)
    horizon: int = Field(default=3, ge=1, le=1000)
    mode: Literal["natural", "position"] = "natural"
    position: Literal["long", "short"] = "long"
    use_csv: bool = False


class ScannerParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategies: List[str] = Field(default_factory=list)
    use_csv: bool = False


__all__ = ["PatternScanParams", "ScannerParams"]
