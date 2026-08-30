import pytest
import mock
from ulauncher.ui.windows.PreferencesUlauncherDialog import PreferencesUlauncherDialog, PrefsApiError
from ulauncher.utils.AutostartPreference import SwitchError


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

    @pytest.fixture(autouse=True)
    def idle_add(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.GLib.idle_add')

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    # pylint: disable=too-many-arguments
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

    # pylint: disable=too-many-arguments
    def test_prefs_set_show_indicator_icon(self, dialog, settings, indicator, idle_add):
        dialog.prefs_set_show_indicator_icon({'query': {'value': 'true'}})
        idle_add.assert_called_with(indicator.switch, True)
        settings.set_property.assert_called_with('show-indicator-icon', True)

        dialog.prefs_set_show_indicator_icon({'query': {'value': '0'}})
        idle_add.assert_called_with(indicator.switch, False)
        settings.set_property.assert_called_with('show-indicator-icon', False)
        settings.save_to_file.assert_called_with()

    def test_prefs_set_hotkey_show_app(self, dialog, ulauncherWindow, settings):
        hotkey = '<Primary>space'
        dialog.prefs_set_hotkey_show_app.original(dialog, {'query': {'value': hotkey}})
        ulauncherWindow.bind_show_app_hotkey.assert_called_with(hotkey)
        settings.set_property.assert_called_with('hotkey-show-app', hotkey)
        settings.save_to_file.assert_called_with()

    def test_prefs_set_autostart(self, dialog, autostart_pref):
        dialog.prefs_set_autostart({'query': {'value': 'true'}})
        autostart_pref.switch.assert_called_with(True)

        dialog.prefs_set_autostart({'query': {'value': 'false'}})
        autostart_pref.switch.assert_called_with(False)

    def test_prefs_set_autostart__keeps_the_switch_error_message(self, dialog, autostart_pref):
        message = 'Could not update the autostart file. Permission denied: /home/user/x.desktop'
        autostart_pref.switch.side_effect = SwitchError(message)
        with pytest.raises(PrefsApiError) as e:
            dialog.prefs_set_autostart({'query': {'value': 'true'}})
        assert str(e.value) == message

    def test_prefs_set_theme_name(self, dialog, settings, ulauncherWindow):
        dialog.prefs_set_theme_name.original(dialog, {'query': {'value': 'light'}})
        settings.set_property.assert_called_with('theme-name', 'light')
        settings.save_to_file.assert_called_with()
        ulauncherWindow.init_theme.assert_called_with()

    def test_prefs_showhotkey_dialog(self, dialog, hotkey_dialog):
        dialog.prefs_showhotkey_dialog.original(dialog, {'query': {'name': 'hotkey-name'}})
        hotkey_dialog.present.assert_called_with()

    def test_prefs_close_hides_dialog_in_the_main_loop(self, dialog, mocker, idle_add):
        hide = mocker.patch.object(dialog, 'hide')
        url_params = {'query': {}}
        dialog.prefs_close(url_params)

        # the request handler runs in a separate thread, so it must not touch the dialog directly
        hide.assert_not_called()
        idle_add.assert_called_with(dialog.prefs_close.original, dialog, url_params)

        dialog.prefs_close.original(dialog, url_params)
        hide.assert_called_with()

    def test_prefs_set_grab_mouse_pointer(self, dialog, settings):
        dialog.prefs_set_grab_mouse_pointer({'query': {'value': 'true'}})
        settings.set_property.assert_called_with('grab-mouse-pointer', True)
        settings.save_to_file.assert_called_with()

    @pytest.mark.with_display
    def test_get_app_hotkey(self, dialog, settings):
        settings.get_property.return_value = '<Primary>B'
        assert dialog.get_app_hotkey() == 'Ctrl+B'

    @pytest.fixture
    def ext_preferences(self, mocker):
        create_instance = mocker.patch(
            'ulauncher.ui.windows.PreferencesUlauncherDialog.ExtensionPreferences.create_instance')
        create_instance.return_value.get.return_value = {'value': 'old'}
        return create_instance.return_value

    @pytest.fixture
    def ext_server(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.ExtensionServer.get_instance').return_value

    def test_prefs_extension_update_prefs__notifies_a_connected_extension(self, dialog, ext_preferences, ext_server):
        controller = ext_server.get_controller.return_value
        dialog.prefs_extension_update_prefs({'query': {'id': 'com.example.ext', 'pref.city': 'new'}})

        ext_preferences.set.assert_called_once_with('city', 'new')
        assert controller.trigger_event.call_count == 1

    def test_prefs_extension_update_prefs__saves_when_the_extension_is_not_connected(
            self, dialog, ext_preferences, ext_server):
        ext_server.get_controller.return_value = None
        dialog.prefs_extension_update_prefs({'query': {'id': 'com.example.ext', 'pref.city': 'new'}})

        ext_preferences.set.assert_called_once_with('city', 'new')

    @pytest.fixture
    def gio(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog.Gio')

    def serve(self, dialog, uri):
        scheme_request = mock.MagicMock()
        scheme_request.get_uri.return_value = uri
        dialog.serve_file(scheme_request).join()
        return scheme_request

    def test_serve_file_percent_decodes_the_path(self, dialog, gio, idle_add):
        scheme_request = self.serve(dialog, 'file2:///home/user/My%20Pics/pic.png')

        gio.file_new_for_path.assert_called_with('/home/user/My Pics/pic.png')
        idle_add.assert_called_with(scheme_request.finish,
                                    gio.file_new_for_path.return_value.read.return_value, -1, 'image/png')

    def test_serve_file_strips_the_null_authority(self, dialog, gio):
        self.serve(dialog, 'file2://null/home/user/pic.png')

        gio.file_new_for_path.assert_called_with('/home/user/pic.png')
