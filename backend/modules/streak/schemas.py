"""Streak domain schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class StreakAnalysisParams(BaseModel):
    """
    연속봉 분석 파라미터 (SSOT: AnalysisContext와 1:1 대응)

    Note:
        필드 추가/수정 시 strategy/streak/common.py의
        AnalysisContext도 함께 수정해야 함
    """

    coin: str = Field(default="SOL", min_length=2, max_length=20)
    interval: str = Field(default="1d", min_length=2, max_length=4)
    n_streak: int = Field(default=6, ge=1, le=50)
    direction: Literal["green", "red"] = "green"
    use_complex_pattern: bool = False
    complex_pattern: Optional[list[int]] = Field(default=None, min_length=2, max_length=20)
    rsi_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    min_total_body_pct: Optional[float] = Field(default=None, ge=0.0)
    ema_200_position: Optional[Literal["above", "below"]] = None
    timezone_offset: Optional[int] = Field(default=None, ge=-12, le=14)

    @field_validator("complex_pattern")
    @classmethod
    def validate_complex_pattern_values(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is None:
            return value
        invalid_values = [v for v in value if v not in (-1, 1)]
        if invalid_values:
            raise ValueError(f"complex_pattern must contain only -1 or 1, got {invalid_values}")
        return value


__all__ = ["StreakAnalysisParams"]
