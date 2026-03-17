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


class ComboFilterParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    direction: Literal["long", "short"] = "long"
    tp_pct: float = Field(default=1.0, ge=0.0, le=100.0)
    horizon: int = Field(default=5, ge=1, le=500)
    rsi_min: float = Field(default=40.0, ge=0.0, le=100.0)
    rsi_max: float = Field(default=60.0, ge=0.0, le=100.0)
    sma_short: int = Field(default=5, ge=1, le=2000)
    sma_long: int = Field(default=20, ge=1, le=2000)
    filter1_type: str = "none"
    filter1_params: Dict[str, Any] = Field(default_factory=dict)
    filter2_type: str = "none"
    filter2_params: Dict[str, Any] = Field(default_factory=dict)
    filter3_type: str = "none"
    filter3_params: Dict[str, Any] = Field(default_factory=dict)
    use_csv: bool = False

    @model_validator(mode="after")
    def validate_combo_filter_relations(self) -> "ComboFilterParams":
        if self.sma_short > self.sma_long:
            raise ValueError("sma_short must be <= sma_long")
        if self.rsi_min > self.rsi_max:
            raise ValueError("rsi_min must be <= rsi_max")
        return self


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


__all__ = [
    "BBMidParams",
    "ComboFilterParams",
    "TrendIndicatorsParams",
    "HybridAnalysisParams",
    "HybridBacktestParams",
    "HybridLiveModeParams",
]
