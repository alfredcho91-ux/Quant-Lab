from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock

from backend.desktop import _server_config, _activate_existing


def test_windowed_desktop_config_does_not_require_console_streams(monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    config = _server_config(5181)

    assert config.use_colors is False
    assert config.log_config is None
    assert config.host == "127.0.0.1"
    assert config.port == 5181


def test_second_launch_activates_native_window_without_opening_browser(monkeypatch):
    instance = SimpleNamespace(existing_url=Mock(return_value="http://127.0.0.1:5182"),
                               existing_metadata=lambda: {"mode": "window", "activation_token": "test-token"})
    urlopen = MagicMock()
    browser = Mock()
    monkeypatch.setattr("backend.desktop.urlopen", urlopen)
    monkeypatch.setattr("backend.desktop.webbrowser.open", browser)
    _activate_existing(instance)
    request = urlopen.call_args.args[0]
    assert request.full_url == "http://127.0.0.1:5182/api/desktop/activate"
    assert request.get_header("X-desktop-token") == "test-token"
    browser.assert_not_called()
