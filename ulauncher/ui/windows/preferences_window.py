from __future__ import annotations

import os
from typing import Any

from gi.repository import Gtk

from ulauncher import paths
from ulauncher.cli import get_cli_args
from ulauncher.ui.preferences_server import PreferencesServer
from ulauncher.utils.webkit2 import WebKit2

cli_args = get_cli_args()


class PreferencesWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(title="Ulauncher Preferences", window_position=Gtk.WindowPosition.CENTER, **kwargs)

        self.set_default_size(1000, 600)
        self._init_webview()
        # Kill the child WebKitNetworkProcess when the window is closed (there's no clean way to do this)
        self.connect("delete-event", self.on_delete)

    def _init_webview(self) -> None:
        settings = WebKit2.Settings(
            enable_developer_extras=cli_args.dev,
            enable_hyperlink_auditing=False,
            enable_page_cache=False,
            enable_webgl=False,
            enable_write_console_messages_to_stdout=True,
            enable_xss_auditor=False,
            hardware_acceleration_policy=WebKit2.HardwareAccelerationPolicy.NEVER,
        )

        server = PreferencesServer()
        self.webview = WebKit2.WebView(settings=settings, web_context=server.context)
        server.client = self.webview
        self.add(self.webview)
        self.webview.show()
        self.load_page()
        # Show right click menu if running with --dev flag
        self.webview.connect("context-menu", lambda *_: not cli_args.dev)

    def load_page(self, page: str | None = "") -> None:
        self.webview.load_uri(f"prefs://{paths.ASSETS}/preferences/index.html#/{page}")

    def present(self, page: str | None = None) -> None:
        if page:
            self.load_page(page)
        super().present()

    def show(self, page: str | None = None) -> None:
        if page:
            self.load_page(page)
        super().show()

    def on_delete(self, *_args: Any, **_kwargs: Any) -> None:
        self.destroy()
        os.system(f"pkill -f WebKitNetworkProcess -P {os.getpid()}")
