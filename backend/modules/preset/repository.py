"""File-backed persistence for saved strategy presets."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from backend.config.settings import LEGACY_PRESETS_FILE, PRESETS_FILE

logger = logging.getLogger(__name__)


def _resolve_path(path: Optional[Path], default: Path) -> Path:
    return path or default


def _read_presets(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Preset file must contain a JSON object")
    return payload


def _write_presets_atomically(path: Path, presets: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Optional[Path] = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(presets, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _migrate_legacy_presets_if_needed(presets_file: Path, legacy_file: Path) -> None:
    if presets_file.exists() or presets_file == legacy_file or not legacy_file.exists():
        return

    try:
        _write_presets_atomically(presets_file, _read_presets(legacy_file))
        logger.info("Migrated legacy presets from %s to %s", legacy_file, presets_file)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("Failed to migrate legacy presets from %s: %s", legacy_file, exc)


def load_presets(
    *,
    presets_file: Optional[Path] = None,
    legacy_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load persisted presets, migrating the legacy root file once when needed."""
    target = _resolve_path(presets_file, PRESETS_FILE)
    legacy = _resolve_path(legacy_file, LEGACY_PRESETS_FILE)
    _migrate_legacy_presets_if_needed(target, legacy)

    if not target.exists():
        return {}

    try:
        return _read_presets(target)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load presets from %s: %s", target, exc)
        return {}


def save_presets(
    presets: Dict[str, Any],
    *,
    presets_file: Optional[Path] = None,
    legacy_file: Optional[Path] = None,
) -> bool:
    """Persist presets with an atomic replace so a partial JSON file is never exposed."""
    target = _resolve_path(presets_file, PRESETS_FILE)
    legacy = _resolve_path(legacy_file, LEGACY_PRESETS_FILE)
    _migrate_legacy_presets_if_needed(target, legacy)

    try:
        _write_presets_atomically(target, presets)
        return True
    except (OSError, TypeError, ValueError) as exc:
        logger.warning("Failed to save presets to %s: %s", target, exc)
        return False


__all__ = ["load_presets", "save_presets"]
