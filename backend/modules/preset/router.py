"""Preset API router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from modules.preset.schemas import PresetSaveRequest
from modules.preset.service import delete_preset_service, get_presets_service, save_preset_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["preset"])


@router.get("/presets")
@handle_api_errors()
async def api_get_presets():
    """Get all saved presets."""
    return await run_in_threadpool(get_presets_service)


@router.post("/presets")
@handle_api_errors()
async def api_save_preset(request: PresetSaveRequest):
    """Save a preset."""
    return await run_in_threadpool(save_preset_service, request.model_dump())


@router.delete("/presets/{name}")
@handle_api_errors()
async def api_delete_preset(name: str):
    """Delete a preset."""
    return await run_in_threadpool(delete_preset_service, name)

