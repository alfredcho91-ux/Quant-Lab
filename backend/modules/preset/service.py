"""Preset API service layer."""

from __future__ import annotations

from typing import Any, Dict

from core.presets import load_presets, save_presets
from utils.error_handler import NotFoundError
from utils.response_builder import success_response
from utils.validators import validate_required_fields


def get_presets_service() -> Dict[str, Any]:
    """Get all saved presets."""
    presets = load_presets()
    return success_response(data=presets)


def save_preset_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update a preset."""
    validate_required_fields(
        payload,
        required_fields=["name", "coin", "interval", "strat_id", "direction"],
        prefix="Preset validation",
    )

    presets = load_presets()
    preset_name = payload["name"]
    presets[preset_name] = {
        "coin": payload["coin"],
        "interval": payload["interval"],
        "strat_id": payload["strat_id"],
        "direction": payload["direction"],
        "params": payload.get("params", {}),
    }
    save_presets(presets)
    return success_response(message="Preset saved")


def delete_preset_service(name: str) -> Dict[str, Any]:
    """Delete preset by name."""
    presets = load_presets()
    if name not in presets:
        raise NotFoundError("Preset", name)
    del presets[name]
    save_presets(presets)
    return success_response(message="Preset deleted")

