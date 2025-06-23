import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from ulauncher.ui.preferences_server import PreferencesServer
from ulauncher.ui.ulauncher_app import UlauncherApp
from ulauncher.utils.settings import Settings

app = UlauncherApp()
settings = Settings.load()


class TestPreferencesServer:
    @pytest.fixture(autouse=True)
    def autostart_pref(self, mocker: MagicMock) -> Any:
        return mocker.patch("ulauncher.ui.preferences_server.SystemdController").return_value

    @pytest.fixture(autouse=True)
    def webview(self, mocker: MagicMock) -> Any:
        return mocker.patch("ulauncher.ui.preferences_server.WebKit2.WebView").return_value

    @pytest.fixture
    def prefs_server(self, webview: MagicMock, autostart_pref: MagicMock) -> PreferencesServer:
        server = PreferencesServer()
        server.autostart_pref = autostart_pref
        server.settings = Settings.load()
        server.client = webview
        return server

    def test_apply_settings_show_tray_icon(self, prefs_server: PreferencesServer) -> None:
        asyncio.run(prefs_server.apply_settings("show_tray_icon", False))
        assert prefs_server.settings.show_tray_icon is False
        assert settings.show_tray_icon is False

    def test_set_autostart(self, prefs_server: PreferencesServer, autostart_pref: MagicMock) -> None:
        prefs_server.apply_autostart(True)
        autostart_pref.toggle.assert_called_with(True)

        prefs_server.apply_autostart(False)
        autostart_pref.toggle.assert_called_with(False)

    def test_set_grab_mouse_pointer_dash_underscore_conversion(self, prefs_server: PreferencesServer) -> None:
        # Verify that setting with dash character is converted to underscore
        asyncio.run(prefs_server.apply_settings("grab-mouse-pointer", True))
        assert settings.grab_mouse_pointer is True
