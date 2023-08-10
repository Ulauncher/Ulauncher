import json
import shutil
from pathlib import Path
from unittest import mock

import pytest
from gi.repository import Gio

from ulauncher.ui.preferences_server import PreferencesServer
from ulauncher.ui.UlauncherApp import UlauncherApp
from ulauncher.utils.Settings import Settings

settings_file = "/tmp/ulauncher-test/pref-settings.json"


def load_json():
    try:
        with open(settings_file) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


class TestPreferencesServer:
    def setup_class(self):
        Path("/tmp/ulauncher-test").mkdir(parents=True, exist_ok=True)

    def teardown_class(self):
        shutil.rmtree("/tmp/ulauncher-test")

    @pytest.fixture(autouse=True)
    def ulauncherWindow(self, mocker):
        app = UlauncherApp.get_instance()
        app.window = mocker.patch("ulauncher.ui.windows.UlauncherWindow.UlauncherWindow").return_value
        app.toggle_appindicator = mock.MagicMock()
        app.bind_hotkey = mock.MagicMock()
        return app.window

    @pytest.fixture(autouse=True)
    def settings_file(self, mocker):
        return mocker.patch("ulauncher.utils.Settings._settings_file", new=settings_file)

    @pytest.fixture(autouse=True)
    def autostart_pref(self, mocker):
        return mocker.patch("ulauncher.ui.preferences_server.SystemdController").return_value

    @pytest.fixture(autouse=True)
    def webview(self, mocker):
        return mocker.patch("ulauncher.ui.preferences_server.WebKit2.WebView").return_value

    @pytest.fixture(autouse=True)
    def hotkey_dialog(self, mocker):
        return mocker.patch("ulauncher.ui.preferences_server.HotkeyDialog").return_value

    @pytest.fixture
    def prefs_server(self, webview, autostart_pref):
        server = PreferencesServer()
        server.autostart_pref = autostart_pref
        server.settings = Settings.load()
        server.client = webview
        return server

    def test_apply_settings_show_indicator_icon(self, prefs_server):
        prefs_server.apply_settings("show_indicator_icon", False)
        Gio.Application.get_default().toggle_appindicator.assert_called_with(False)
        assert prefs_server.settings.show_indicator_icon is False
        assert load_json().get("show_indicator_icon") is False

    def test_set_hotkey_show_app(self, prefs_server):
        hotkey = "<Primary>space"
        prefs_server.set_hotkey_show_app.original(prefs_server, hotkey)
        Gio.Application.get_default().bind_hotkey.assert_called_with(hotkey)
        assert prefs_server.settings.hotkey_show_app == hotkey
        assert load_json().get("hotkey_show_app") == hotkey

    def test_set_autostart(self, prefs_server, autostart_pref):
        prefs_server.apply_autostart(True)
        autostart_pref.toggle.assert_called_with(True)

        prefs_server.apply_autostart(False)
        autostart_pref.toggle.assert_called_with(False)

    def test_set_theme_name(self, prefs_server, ulauncherWindow):
        prefs_server.apply_settings("theme_name", "lime")
        assert prefs_server.settings.theme_name == "lime"
        assert load_json().get("theme_name") == "lime"
        ulauncherWindow.apply_theme.assert_called_with()

    def test_show_hotkey_dialog(self, prefs_server, hotkey_dialog):
        prefs_server.show_hotkey_dialog.original(prefs_server)
        hotkey_dialog.present.assert_called_with()

    def test_set_grab_mouse_pointer_dash_underscore_conversion(self, prefs_server):
        prefs_server.apply_settings("grab-mouse-pointer", True)
        # Verify that setting with dash character is converted to underscore
        assert load_json().get("grab_mouse_pointer") is True
