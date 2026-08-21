"""Preset domain schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PresetSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    coin: str = Field(min_length=2, max_length=20)
    interval: str = Field(min_length=2, max_length=4)
    strat_id: str = Field(min_length=1, max_length=50)
    direction: str = Field(min_length=1, max_length=20)
    params: Dict[str, Any]


class PresetPayload(BaseModel):
    coin: str
    interval: str
    strat_id: str
    direction: str
    params: Dict[str, Any]


class PresetsEnvelope(BaseModel):
    success: bool
    data: Dict[str, PresetPayload]


class PresetMutationEnvelope(BaseModel):
    success: bool
    message: Optional[str] = None


__all__ = [
    "PresetMutationEnvelope",
    "PresetsEnvelope",
    "PresetSaveRequest",
]
