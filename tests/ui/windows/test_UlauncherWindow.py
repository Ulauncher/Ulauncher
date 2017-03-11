import pytest
import mock
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow


class TestUlauncherWindow:

    @pytest.fixture(autouse=True)
    def init_styles(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.init_styles')

    @pytest.fixture(autouse=True)
    def start_sync(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.start_app_watcher')

    @pytest.fixture(autouse=True)
    def show_notification(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.show_notification')

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Settings.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extRunner(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.ExtensionRunner.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extServer(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.ExtensionServer.get_instance').return_value

    @pytest.fixture(autouse=True)
    def Keybinder(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Keybinder')

    @pytest.fixture
    def window(self, mocker):
        return UlauncherWindow()

    @pytest.mark.with_display
    def test_bind_show_app_hotkey(self, window, Keybinder, show_notification):
        accel_name = '<Primary><Alt>f'
        window.bind_show_app_hotkey(accel_name)
        Keybinder.bind.assert_called_with(accel_name, window.cb_toggle_visibility)

        # bind another one
        # this time Ulauncher should unbind previous key
        new_accel_name = '<Primary><Alt>r'
        window.bind_show_app_hotkey(new_accel_name)
        Keybinder.unbind.assert_called_with(accel_name)
        Keybinder.bind.assert_called_with(new_accel_name, window.cb_toggle_visibility)
        show_notification.assert_called_with('Ulauncher', 'Hotkey is set to Ctrl+Alt+R')
