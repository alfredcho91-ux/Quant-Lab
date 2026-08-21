from __future__ import annotations

import json

from backend.modules.preset import repository


def test_load_presets_migrates_legacy_file_to_project_storage(tmp_path):
    legacy_file = tmp_path / "presets.json"
    presets_file = tmp_path / "data" / "presets.json"
    legacy_presets = {"BTC 4h": {"coin": "BTC", "interval": "4h"}}
    legacy_file.write_text(json.dumps(legacy_presets), encoding="utf-8")

    result = repository.load_presets(
        presets_file=presets_file,
        legacy_file=legacy_file,
    )

    assert result == legacy_presets
    assert json.loads(presets_file.read_text(encoding="utf-8")) == legacy_presets
    assert json.loads(legacy_file.read_text(encoding="utf-8")) == legacy_presets


def test_load_presets_keeps_existing_project_storage(tmp_path):
    legacy_file = tmp_path / "presets.json"
    presets_file = tmp_path / "data" / "presets.json"
    legacy_file.write_text('{"legacy": {}}', encoding="utf-8")
    presets_file.parent.mkdir(parents=True)
    presets_file.write_text('{"current": {}}', encoding="utf-8")

    result = repository.load_presets(
        presets_file=presets_file,
        legacy_file=legacy_file,
    )

    assert result == {"current": {}}
    assert json.loads(legacy_file.read_text(encoding="utf-8")) == {"legacy": {}}


def test_save_presets_writes_a_complete_file_without_temp_artifacts(tmp_path):
    presets_file = tmp_path / "data" / "presets.json"
    presets = {"ETH 1h": {"coin": "ETH", "interval": "1h"}}

    assert repository.save_presets(presets, presets_file=presets_file) is True
    assert json.loads(presets_file.read_text(encoding="utf-8")) == presets
    assert list(presets_file.parent.glob(".presets.json.*.tmp")) == []


def test_save_presets_cleans_up_temporary_file_after_serialization_failure(tmp_path):
    presets_file = tmp_path / "data" / "presets.json"
    legacy_file = tmp_path / "legacy" / "presets.json"

    assert (
        repository.save_presets(
            {"invalid": object()},
            presets_file=presets_file,
            legacy_file=legacy_file,
        )
        is False
    )
    assert not presets_file.exists()
    assert list(presets_file.parent.glob(".presets.json.*.tmp")) == []
