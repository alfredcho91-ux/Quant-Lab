from datetime import date, datetime, timezone
from math import prod
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Distance(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mode: Literal["fixed_pct", "atr", "mtr", "wick_mean", "wick_median", "wick_percentile", "breakout_percentile", "mae_percentile"] = "fixed_pct"
    percentile: float = Field(default=95, ge=50, le=99)


class LabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    coin: Literal["BTC", "ETH", "SOL"] = "BTC"
    start: date
    end: date
    reference_interval: Literal["1d", "1w"] = "1d"
    execution_interval: Literal["5m", "15m", "1h", "4h"] = "15m"
    direction: Literal["Long", "Short", "Both"] = "Short"
    reference: Literal["previous_extreme", "previous_close", "previous_open", "wick_extreme", "confirmed_swing"] = "previous_extreme"
    lookback: int = Field(default=14, ge=1, le=365)
    entry: Distance = Field(default_factory=Distance)
    stop: Distance = Field(default_factory=Distance)
    target_mode: Literal["fixed_pct", "atr", "mtr", "r_multiple", "reference", "price"] = "fixed_pct"
    entry_values: list[float] = Field(default_factory=lambda: [0.5], min_length=1, max_length=10)
    stop_values: list[float] = Field(default_factory=lambda: [0.5], min_length=1, max_length=10)
    target_values: list[float] = Field(default_factory=lambda: [1.5], min_length=1, max_length=10)
    exit_rule: Literal["period_end", "holding_hours"] = "period_end"
    holding_hours: int = Field(default=24, ge=1, le=720)
    max_entries_per_period: int = Field(default=1, ge=1, le=5)
    fee_bps: float = Field(default=5, ge=0, le=100)
    slippage_bps: float = Field(default=2, ge=0, le=100)
    initial_equity: float = Field(default=10000, ge=100, le=1e9)
    sizing: Literal["risk", "notional"] = "risk"
    risk_pct: float = Field(default=1, gt=0, le=10)
    allocation_pct: float = Field(default=100, gt=0, le=100)
    train_ratio: float = Field(default=0.7, ge=0.5, le=0.85)
    max_drawdown_pct: float = Field(default=30, gt=0, le=100)
    min_trades: int = Field(default=5, ge=3, le=100)

    @model_validator(mode="after")
    def relationships(self):
        import math
        if self.end < self.start or (self.end - self.start).days > 365:
            raise ValueError("Choose an inclusive UTC date range of at most 366 days")
        if self.end > datetime.now(timezone.utc).date():
            raise ValueError("Future dates are not supported")
        step = {"5m": 5, "15m": 15, "1h": 60, "4h": 240}[self.execution_interval]
        bars = ((self.end - self.start).days + 1) * 1440 // step
        combinations = prod(map(len, (self.entry_values, self.stop_values, self.target_values)))
        if bars > 30000 or combinations > 125 or bars * combinations * self.max_entries_per_period > 3_000_000:
            raise ValueError("Research budget exceeded: <=30,000 execution bars, <=125 combinations, <=3,000,000 bar-combination-entry operations")
        for values, zero in ((self.entry_values, True), (self.stop_values, False), (self.target_values, False)):
            if len(set(values)) != len(values) or any(not math.isfinite(v) or v < 0 or (not zero and v == 0) or v > 1e7 for v in values):
                raise ValueError("Grid values must be unique, finite and positive (entry may be zero), <=10,000,000")
            values.sort()
        if self.entry.mode == "mae_percentile":
            raise ValueError("Conditional MAE can set stops, not the entry that defines its own sample")
        if self.stop.mode == "mae_percentile" and self.min_trades > self.lookback:
            raise ValueError("Conditional MAE lookback must cover the minimum sample count")
        if self.exit_rule == "holding_hours" and self.holding_hours * 60 % step:
            raise ValueError("Holding time must align with complete execution candles")
        if self.target_mode == "reference" and len(self.target_values) != 1:
            raise ValueError("Reference-return target has one level, not a target-value grid")
        return self
