from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from backend.desktop_instance import DesktopInstance


def test_desktop_instance_prevents_second_process_lock(tmp_path):
    first = DesktopInstance(tmp_path)
    second = DesktopInstance(tmp_path)

    assert first.acquire() is True
    try:
        assert second.acquire() is False
    finally:
        first.release()

    assert second.acquire() is True
    second.release()


def test_desktop_instance_publishes_and_removes_metadata(tmp_path):
    instance = DesktopInstance(tmp_path)
    assert instance.acquire() is True

    instance.publish("http://127.0.0.1:5181")
    assert instance.metadata_path.read_text(encoding="utf-8").find("127.0.0.1:5181") >= 0

    instance.release()
    assert not instance.metadata_path.exists()


def test_native_metadata_preserves_activation_details(tmp_path):
    with DesktopInstance(tmp_path) as instance:
        instance.publish("http://127.0.0.1:5182", mode="window", activation_token="test-token")
        assert instance.existing_metadata()["mode"] == "window"
        assert instance.existing_metadata()["activation_token"] == "test-token"


@pytest.mark.parametrize("url", ["https://example.org", "file:///C:/test", "http://evil@127.0.0.1:5182", "http://127.0.0.1:bad"])
def test_existing_url_never_contacts_untrusted_metadata(tmp_path, monkeypatch, url):
    instance = DesktopInstance(tmp_path)
    instance.metadata_path.write_text(json.dumps({"url": url}), encoding="utf-8")
    readiness = Mock(return_value=True)
    monkeypatch.setattr("backend.desktop_instance._server_is_ready", readiness)
    assert instance.existing_url(timeout_seconds=.01) is None
    readiness.assert_not_called()
