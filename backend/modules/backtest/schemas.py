"""Backtest domain schemas."""

from typing import Optional, Literal

from pydantic import BaseModel, Field, model_validator


class BacktestParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategy_id: str = Field(default="Connors", min_length=1, max_length=50)
    direction: Literal["Long", "Short"] = "Long"
    tp_pct: float = Field(default=2.0, gt=0.0, le=100.0)
    sl_pct: float = Field(default=1.0, gt=0.0, le=100.0)
    max_bars: int = Field(default=48, ge=1, le=10000)
    leverage: int = Field(default=10, ge=1, le=125)
    entry_fee_pct: float = Field(default=0.04, ge=0.0, le=5.0)
    exit_fee_pct: float = Field(default=0.04, ge=0.0, le=5.0)
    rsi_ob: int = Field(default=70, ge=0, le=100)
    sma_main_len: int = Field(default=200, ge=1, le=5000)
    sma1_len: int = Field(default=20, ge=1, le=5000)
    sma2_len: int = Field(default=60, ge=1, le=5000)
    adx_thr: int = Field(default=25, ge=0, le=100)
    donch: int = Field(default=20, ge=1, le=5000)
    bb_length: int = Field(default=20, ge=1, le=5000)
    bb_std_mult: float = Field(default=2.0, gt=0.0, le=10.0)
    atr_length: int = Field(default=20, ge=1, le=5000)
    kc_mult: float = Field(default=1.5, gt=0.0, le=10.0)
    vol_ma_length: int = Field(default=20, ge=1, le=5000)
    vol_spike_k: float = Field(default=2.0, gt=0.0, le=100.0)
    macd_fast: int = Field(default=12, ge=1, le=5000)
    macd_slow: int = Field(default=26, ge=1, le=5000)
    macd_signal: int = Field(default=9, ge=1, le=5000)
    use_csv: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if "sma_main_len" not in payload and "ema_len" in payload:
                payload["sma_main_len"] = payload.get("ema_len")
            payload.pop("rsi2_ob", None)
            return payload
        return data

    @model_validator(mode="after")
    def validate_parameter_relations(self) -> "BacktestParams":
        if self.sma1_len > self.sma2_len:
            raise ValueError("sma1_len must be <= sma2_len")
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be < macd_slow")
        return self


class AdvancedBacktestParams(BaseModel):
    coin: str = Field(default="BTC", min_length=2, max_length=20)
    interval: str = Field(default="1h", min_length=2, max_length=4)
    strategy_id: str = Field(default="Connors", min_length=1, max_length=50)
    direction: Literal["Long", "Short"] = "Long"
    tp_pct: float = Field(default=2.0, gt=0.0, le=100.0)
    sl_pct: float = Field(default=1.0, gt=0.0, le=100.0)
    max_bars: int = Field(default=48, ge=1, le=10000)
    leverage: int = Field(default=10, ge=1, le=125)
    entry_fee_pct: float = Field(default=0.04, ge=0.0, le=5.0)
    exit_fee_pct: float = Field(default=0.04, ge=0.0, le=5.0)
    rsi_ob: int = Field(default=70, ge=0, le=100)
    sma_main_len: int = Field(default=200, ge=1, le=5000)
    sma1_len: int = Field(default=20, ge=1, le=5000)
    sma2_len: int = Field(default=60, ge=1, le=5000)
    adx_thr: int = Field(default=25, ge=0, le=100)
    donch: int = Field(default=20, ge=1, le=5000)
    bb_length: int = Field(default=20, ge=1, le=5000)
    bb_std_mult: float = Field(default=2.0, gt=0.0, le=10.0)
    atr_length: int = Field(default=20, ge=1, le=5000)
    kc_mult: float = Field(default=1.5, gt=0.0, le=10.0)
    vol_ma_length: int = Field(default=20, ge=1, le=5000)
    vol_spike_k: float = Field(default=2.0, gt=0.0, le=100.0)
    macd_fast: int = Field(default=12, ge=1, le=5000)
    macd_slow: int = Field(default=26, ge=1, le=5000)
    macd_signal: int = Field(default=9, ge=1, le=5000)
    use_csv: bool = False
    train_ratio: float = Field(default=0.7, gt=0.0, lt=1.0)
    monte_carlo_runs: int = Field(default=1000, ge=100, le=100000)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data):
        if isinstance(data, dict):
            payload = dict(data)
            if "sma_main_len" not in payload and "ema_len" in payload:
                payload["sma_main_len"] = payload.get("ema_len")
            payload.pop("rsi2_ob", None)
            return payload
        return data

    @model_validator(mode="after")
    def validate_parameter_relations(self) -> "AdvancedBacktestParams":
        if self.sma1_len > self.sma2_len:
            raise ValueError("sma1_len must be <= sma2_len")
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be < macd_slow")
        return self


__all__ = ["BacktestParams", "AdvancedBacktestParams"]
