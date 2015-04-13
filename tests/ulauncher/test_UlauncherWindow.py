import pytest
import mock
from ulauncher.UlauncherWindow import UlauncherWindow


class TestUlauncherWindow:

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.UlauncherWindow.getSettings').return_value

    @pytest.fixture(autouse=True)
    def Keybinder(self, mocker):
        return mocker.patch('ulauncher.UlauncherWindow.Keybinder')

    @pytest.fixture
    def window(self, mocker):
        return UlauncherWindow()

    def test_bind_show_app_hotkey(self, window, Keybinder):
        accel_name = '<Primary><Alt>f'
        window.bind_show_app_hotkey(accel_name)
        Keybinder.bind.assert_called_with(accel_name, window.cb_toggle_visibility)

        # bind another one
        # this time Ulauncher should unbind previous key
        new_accel_name = '<Primary><Alt>r'
        window.bind_show_app_hotkey(new_accel_name)
        Keybinder.unbind.assert_called_with(accel_name)
        Keybinder.bind.assert_called_with(new_accel_name, window.cb_toggle_visibility)
