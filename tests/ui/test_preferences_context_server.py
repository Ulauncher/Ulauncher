from unittest import mock
import pytest
from ulauncher.ui.UlauncherApp import UlauncherApp
from ulauncher.ui.preferences_context_server import PreferencesContextServer


class TestPreferencesContextServer:

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.preferences_context_server.Settings.get_instance').return_value

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
    def context_server(self, settings, webview, autostart_pref, ulauncherWindow):
        app = UlauncherApp()
        app.window = ulauncherWindow
        app.toggle_appindicator = mock.MagicMock()
        app.bind_hotkey = mock.MagicMock()
        server = PreferencesContextServer(app)
        server.autostart_pref = autostart_pref
        server.settings = settings
        server.client = webview
        return server

    # pylint: disable=too-many-arguments
    def test_apply_settings_show_indicator_icon(self, context_server, settings):
        context_server.apply_settings({'property': 'show-indicator-icon', 'value': True})
        context_server.application.toggle_appindicator.assert_called_with(True)
        settings.set_property.assert_called_with('show-indicator-icon', True)

        context_server.apply_settings({'property': 'show-indicator-icon', 'value': False})
        context_server.application.toggle_appindicator.assert_called_with(False)
        settings.set_property.assert_called_with('show-indicator-icon', False)

    def test_set_hotkey_show_app(self, context_server, settings):
        hotkey = '<Primary>space'
        context_server.set_hotkey_show_app.original(context_server, {'value': hotkey})
        context_server.application.bind_hotkey.assert_called_with(hotkey)
        settings.set_property.assert_called_with('hotkey-show-app', hotkey)

    def test_set_autostart(self, context_server, autostart_pref):
        context_server.apply_autostart(True)
        autostart_pref.switch.assert_called_with(True)

        context_server.apply_autostart(False)
        autostart_pref.switch.assert_called_with(False)

    def test_set_theme_name(self, context_server, settings, ulauncherWindow):
        context_server.apply_settings({'property': 'theme-name', 'value': 'light'})
        settings.set_property.assert_called_with('theme-name', 'light')
        ulauncherWindow.init_theme.assert_called_with()

    def test_show_hotkey_dialog(self, context_server, hotkey_dialog):
        context_server.show_hotkey_dialog.original(context_server, {})
        hotkey_dialog.present.assert_called_with()

    def test_set_grab_mouse_pointer(self, context_server, settings):
        context_server.apply_settings({'property': 'grab-mouse-pointer', 'value': True})
        settings.set_property.assert_called_with('grab-mouse-pointer', True)
