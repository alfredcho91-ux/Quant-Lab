"""Windows WebView2 shell; domain logic remains in the existing HTTP application."""
from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit


def _origin(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username or parsed.password:
            return None
        return parsed.scheme, parsed.hostname, parsed.port
    except ValueError:
        return None


class DesktopWindow:
    def __init__(self, url, sample_process):
        self.url = url
        self.sample_process = sample_process
        self.window = None
        self._loaded = threading.Event()
        self._allow_close = threading.Event()
        self._closing = threading.Lock()
        self._activate_pending = threading.Event()

    def allows_navigation(self, url):
        origin = _origin(url)
        return origin is not None and origin in {_origin(self.url), _origin(self.sample_process.url or "")}

    def _navigation_starting(self, _sender, args):
        if self.allows_navigation(str(args.Uri)):
            return
        args.Cancel = True
        if args.IsUserInitiated and urlsplit(str(args.Uri)).scheme in {"http", "https"}:
            webbrowser.open(str(args.Uri), new=2)

    def _before_show(self):
        self.window.native.webview.NavigationStarting += self._navigation_starting

    def _on_loaded(self):
        self._loaded.set()
        if self._activate_pending.is_set():
            self.activate()

    def activate(self):
        self._activate_pending.set()
        if self.window is not None and self._loaded.is_set():
            self.window.restore()
            self.window.show()
            self._activate_pending.clear()

    def request_close(self):
        if self._closing.acquire(blocking=False):
            threading.Thread(target=self._check_close, daemon=True).start()

    def _check_close(self):
        try:
            if self._loaded.is_set():
                # Reuse the same dirty/pending guard as in-app navigation.
                allowed = self.window.evaluate_js(
                    "window.dispatchEvent(new Event('app-before-navigate', {cancelable: true}))"
                )
                if allowed is not True:
                    return
            self._allow_close.set()
            self.window.destroy()
        finally:
            self._closing.release()

    def _on_closing(self):
        if self._allow_close.is_set():
            return True
        self.request_close()
        return False

    def run(self, storage_path: Path):
        import webview

        self.window = webview.create_window(
            "Quant Lab", self.url, width=1440, height=960, min_size=(960, 640),
            background_color="#151a22", text_select=True, zoomable=True,
        )
        self.window.events.before_show += self._before_show
        self.window.events.before_load += self._loaded.clear
        self.window.events.loaded += self._on_loaded
        self.window.events.closing += self._on_closing
        storage_path.mkdir(parents=True, exist_ok=True)
        # Fail visibly if WebView2 is missing; never use the legacy MSHTML engine.
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(storage_path))
