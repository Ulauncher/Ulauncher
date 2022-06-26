import json
from unittest import mock
import pytest
from ulauncher.utils.Settings import Settings
from ulauncher.ui.UlauncherApp import UlauncherApp
from ulauncher.ui.preferences_context_server import PreferencesContextServer

settings_file = '/tmp/ulauncher-test/pref-ctx-settings.json'


def check_json_prop(name):
    with open(settings_file) as f:
        return json.load(f).get(name)


class TestPreferencesContextServer:

    @pytest.fixture(autouse=True)
    def ulauncherWindow(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.get_instance').return_value

    @pytest.fixture(autouse=True)
    def autostart_pref(self, mocker):
        return mocker.patch('ulauncher.ui.preferences_context_server.UlauncherSystemdController').return_value

    @pytest.fixture(autouse=True)
    def webview(self, mocker):
        return mocker.patch('ulauncher.ui.preferences_context_server.WebKit2.WebView').return_value

    @pytest.fixture(autouse=True)
    def hotkey_dialog(self, mocker):
        return mocker.patch('ulauncher.ui.preferences_context_server.HotkeyDialog').return_value

    # pylint: disable=too-many-arguments
    @pytest.fixture
    def context_server(self, webview, autostart_pref, ulauncherWindow):
        app = UlauncherApp()
        app.window = ulauncherWindow
        app.toggle_appindicator = mock.MagicMock()
        app.bind_hotkey = mock.MagicMock()
        server = PreferencesContextServer(app)
        server.autostart_pref = autostart_pref
        server.settings = Settings.new_from_file(settings_file)
        server.client = webview
        return server

    # pylint: disable=too-many-arguments
    def test_apply_settings_show_indicator_icon(self, context_server):
        context_server.apply_settings({'property': 'show_indicator_icon', 'value': True})
        context_server.application.toggle_appindicator.assert_called_with(True)
        assert context_server.settings.show_indicator_icon is True
        assert check_json_prop("show_indicator_icon") is True

        context_server.apply_settings({'property': 'show_indicator_icon', 'value': False})
        context_server.application.toggle_appindicator.assert_called_with(False)
        assert context_server.settings.show_indicator_icon is False
        assert check_json_prop("show_indicator_icon") is False

    def test_set_hotkey_show_app(self, context_server):
        hotkey = '<Primary>space'
        context_server.set_hotkey_show_app.original(context_server, {'value': hotkey})
        context_server.application.bind_hotkey.assert_called_with(hotkey)
        assert context_server.settings.hotkey_show_app == hotkey
        assert check_json_prop("hotkey_show_app") == hotkey

    def test_set_autostart(self, context_server, autostart_pref):
        context_server.apply_autostart(True)
        autostart_pref.switch.assert_called_with(True)

        context_server.apply_autostart(False)
        autostart_pref.switch.assert_called_with(False)

    def test_set_theme_name(self, context_server, ulauncherWindow):
        context_server.apply_settings({'property': 'theme_name', 'value': 'lime'})
        assert context_server.settings.theme_name == 'lime'
        assert check_json_prop("theme_name") == 'lime'
        ulauncherWindow.init_theme.assert_called_with()

    def test_show_hotkey_dialog(self, context_server, hotkey_dialog):
        context_server.show_hotkey_dialog.original(context_server, {})
        hotkey_dialog.present.assert_called_with()

    def test_set_grab_mouse_pointer_dash_underscore_conversion(self, context_server):
        context_server.apply_settings({'property': 'grab-mouse-pointer', 'value': True})
        # Verify that setting with dash character is converted to underscore
        assert check_json_prop("grab_mouse_pointer") is True
