import pytest
import mock
from ulauncher.ui.windows.PreferencesUlauncherDialog import PreferencesUlauncherDialog
from gi.repository import Gtk


class TestPreferencesUlauncherDialog:

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.Settings.get_instance').return_value

    @pytest.fixture(autouse=True)
    def indicator(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.AppIndicator.get_instance').return_value

    @pytest.fixture(autouse=True)
    def ulauncherWindow(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.get_instance').return_value

    @pytest.fixture(autouse=True)
    def autostart_pref(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.AutostartPreference').return_value

    @pytest.fixture(autouse=True)
    def webview(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.WebKit2.WebView').return_value

    @pytest.fixture(autouse=True)
    def hotkey_dialog(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.HotkeyDialog').return_value

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture
    def dialog(self, builder, mocker, settings, webview, autostart_pref, hotkey_dialog):
        mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.PreferencesUlauncherDialog.finish_initializing')
        dialog = PreferencesUlauncherDialog()
        dialog.settings = settings
        dialog.webview = webview
        dialog.autostart_pref = autostart_pref
        dialog.hotkey_dialog = hotkey_dialog
        dialog.ui = mock.MagicMock()
        dialog.builder = builder
        return dialog

    def test_prefs_set_show_indicator_icon(self, dialog, builder, settings, indicator):
        dialog.prefs_set_show_indicator_icon({'query': {'value': 'true'}})
        indicator.show.assert_called_with()
        settings.set_property.assert_called_with('show-indicator-icon', True)

        dialog.prefs_set_show_indicator_icon({'query': {'value': '0'}})
        indicator.hide.assert_called_with()
        settings.set_property.assert_called_with('show-indicator-icon', False)
        settings.save_to_file.assert_called_with()

    def test_prefs_set_hotkey_show_app(self, dialog, ulauncherWindow, settings):
        hotkey = '<Primary>space'
        dialog.prefs_set_hotkey_show_app({'query': {'value': hotkey}})
        ulauncherWindow.bind_show_app_hotkey.assert_called_with(hotkey)
        settings.set_property.assert_called_with('hotkey-show-app', hotkey)
        settings.save_to_file.assert_called_with()

    def test_prefs_set_autostart(self, dialog, autostart_pref):
        dialog.prefs_set_autostart({'query': {'value': 'true'}})
        autostart_pref.switch.assert_called_with(True)

        dialog.prefs_set_autostart({'query': {'value': 'false'}})
        autostart_pref.switch.assert_called_with(False)

    def test_prefs_set_theme_name(self, dialog, settings, ulauncherWindow):
        dialog.prefs_set_theme_name({'query': {'value': 'light'}})
        settings.set_property.assert_called_with('theme-name', 'light')
        settings.save_to_file.assert_called_with()
        ulauncherWindow.init_theme.assert_called_with()

    def test_prefs_showhotkey_dialog(self, dialog, hotkey_dialog):
        dialog.prefs_showhotkey_dialog({'query': {'name': 'hotkey-name'}})
        hotkey_dialog.present.assert_called_with()

    @pytest.mark.with_display
    def test_get_app_hotkey(self, dialog, settings):
        settings.get_property.return_value = '<Primary>B'
        assert dialog.get_app_hotkey() == 'Ctrl+B'
