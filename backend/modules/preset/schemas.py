"""Preset domain schemas."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class PresetSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    coin: str = Field(min_length=2, max_length=20)
    interval: str = Field(min_length=2, max_length=4)
    strat_id: str = Field(min_length=1, max_length=50)
    direction: str = Field(min_length=1, max_length=20)
    params: Dict[str, Any]


__all__ = ["PresetSaveRequest"]

