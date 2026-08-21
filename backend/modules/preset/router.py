"""Preset API router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.modules.preset.schemas import PresetMutationEnvelope, PresetsEnvelope, PresetSaveRequest
from backend.modules.preset.service import delete_preset_service, get_presets_service, save_preset_service
from backend.utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["preset"])


@router.get("/presets", response_model=PresetsEnvelope)
@handle_api_errors()
async def api_get_presets():
    """Get all saved presets."""
    return await run_in_threadpool(get_presets_service)


@router.post("/presets", response_model=PresetMutationEnvelope)
@handle_api_errors()
async def api_save_preset(request: PresetSaveRequest):
    """Save a preset."""
    return await run_in_threadpool(save_preset_service, request.model_dump())


@router.delete("/presets/{name}", response_model=PresetMutationEnvelope)
@handle_api_errors()
async def api_delete_preset(name: str):
    """Delete a preset."""
    return await run_in_threadpool(delete_preset_service, name)
