# routes/preset.py
"""Preset API 엔드포인트"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from core.presets import load_presets, save_presets
from utils.decorators import handle_api_errors
from utils.response_builder import success_response
from utils.validators import validate_required_fields
from utils.error_handler import NotFoundError

router = APIRouter(prefix="/api", tags=["preset"])


class PresetSaveRequest(BaseModel):
    name: str
    coin: str
    interval: str
    strat_id: str
    direction: str
    params: Dict[str, Any]


@router.get("/presets")
@handle_api_errors()
async def api_get_presets():
    """Get all saved presets"""
    presets = load_presets()
    return success_response(data=presets)


@router.post("/presets")
@handle_api_errors()
async def api_save_preset(request: PresetSaveRequest):
    """Save a preset"""
    # 검증
    validate_required_fields(
        request.model_dump(),
        required_fields=["name", "coin", "interval", "strat_id", "direction"],
        prefix="Preset validation",
    )
    
    presets = load_presets()
    presets[request.name] = {
        "coin": request.coin,
        "interval": request.interval,
        "strat_id": request.strat_id,
        "direction": request.direction,
        "params": request.params,
    }
    save_presets(presets)
    return success_response(message="Preset saved")


@router.delete("/presets/{name}")
@handle_api_errors()
async def api_delete_preset(name: str):
    """Delete a preset"""
    presets = load_presets()
    if name not in presets:
        raise NotFoundError("Preset", name)
    
    del presets[name]
    save_presets(presets)
    return success_response(message="Preset deleted")
