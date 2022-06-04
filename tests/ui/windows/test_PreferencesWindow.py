from unittest import mock
import pytest
from ulauncher.ui.windows.PreferencesWindow import PreferencesWindow


class TestPreferencesWindow:

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.Settings.get_instance').return_value

    @pytest.fixture(autouse=True)
    def indicator(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.AppIndicator.get_instance').return_value

    @pytest.fixture(autouse=True)
    def ulauncherWindow(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.get_instance').return_value

    @pytest.fixture(autouse=True)
    def autostart_pref(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.AutostartPreference').return_value

    @pytest.fixture(autouse=True)
    def webview(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.WebKit2.WebView').return_value

    @pytest.fixture(autouse=True)
    def hotkey_dialog(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.HotkeyDialog').return_value

    @pytest.fixture(autouse=True)
    def idle_add(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesWindow.GLib.idle_add')

    # pylint: disable=too-many-arguments
    @pytest.fixture
    def preferences_window(self, mocker, settings, webview, autostart_pref, hotkey_dialog):
        mocker.patch('ulauncher.ui.windows.PreferencesWindow.PreferencesWindow._init_webview')
        win = PreferencesWindow()
        win.settings = settings
        win.webview = webview
        win.autostart_pref = autostart_pref
        win.hotkey_dialog = hotkey_dialog
        win.ui = mock.MagicMock()
        return win

    # pylint: disable=too-many-arguments
    def test_prefs_set_show_indicator_icon(self, preferences_window, settings, indicator, idle_add):
        preferences_window.prefs_set({'property': 'show-indicator-icon', 'value': True})
        idle_add.assert_called_with(indicator.switch, True)
        settings.set_property.assert_called_with('show-indicator-icon', True)

        preferences_window.prefs_set({'property': 'show-indicator-icon', 'value': False})
        idle_add.assert_called_with(indicator.switch, False)
        settings.set_property.assert_called_with('show-indicator-icon', False)

    def test_prefs_set_hotkey_show_app(self, preferences_window, ulauncherWindow, settings):
        hotkey = '<Primary>space'
        preferences_window.prefs_set_hotkey_show_app.original(preferences_window, {'value': hotkey})
        ulauncherWindow.bind_hotkey.assert_called_with(hotkey)
        settings.set_property.assert_called_with('hotkey-show-app', hotkey)

    def test_prefs_set_autostart(self, preferences_window, autostart_pref):
        preferences_window.prefs_set_autostart(True)
        autostart_pref.switch.assert_called_with(True)

        preferences_window.prefs_set_autostart(False)
        autostart_pref.switch.assert_called_with(False)

    def test_prefs_set_theme_name(self, preferences_window, settings, ulauncherWindow):
        preferences_window.prefs_set({'property': 'theme-name', 'value': 'light'})
        settings.set_property.assert_called_with('theme-name', 'light')
        ulauncherWindow.init_theme.assert_called_with()

    def test_prefs_showhotkey_dialog(self, preferences_window, hotkey_dialog):
        preferences_window.prefs_showhotkey_dialog.original(preferences_window, {'name': 'hotkey-name'})
        hotkey_dialog.present.assert_called_with()

    def test_prefs_set_grab_mouse_pointer(self, preferences_window, settings):
        preferences_window.prefs_set({'property': 'grab-mouse-pointer', 'value': True})
        settings.set_property.assert_called_with('grab-mouse-pointer', True)

    @pytest.mark.with_display
    def test_get_app_hotkey(self, preferences_window, settings):
        settings.get_property.return_value = '<Primary>B'
        assert preferences_window.get_app_hotkey() == 'Ctrl+B'
