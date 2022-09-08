from unittest import mock
import pytest
from gi.repository import Gtk

from ulauncher.api.result import Result
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow


class TestUlauncherWindow:

    @pytest.fixture(autouse=True)
    def init_styles(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.init_styles')

    @pytest.fixture(autouse=True)
    def is_x11_compatible(self, mocker):
        wayland_compat = mocker.patch('ulauncher.ui.windows.UlauncherWindow.IS_X11_COMPATIBLE')
        wayland_compat.return_value = False
        return wayland_compat

    @pytest.fixture(autouse=True)
    def Theme(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Theme')

    @pytest.fixture(autouse=True)
    def load_available_themes(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.load_available_themes')

    @pytest.fixture(autouse=True)
    def new_image_from_surface(self, mocker):
        mocked = mocker.patch('ulauncher.ui.windows.UlauncherWindow.Gtk.Image.new_from_pixbuf')
        mocked.return_value = Gtk.Image()
        return mocked

    @pytest.fixture(autouse=True)
    def load_icon_surface(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.load_icon_surface')

    @pytest.fixture(autouse=True)
    def AppResult(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.AppResult.get_most_frequent').return_value

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Settings.load').return_value

    @pytest.fixture(autouse=True)
    def get_scr_geometry(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.get_monitor')

    @pytest.fixture(autouse=True)
    def Keybinder(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Keybinder')

    @pytest.fixture
    def GtkBuilder(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Gtk').Builder

    @pytest.fixture
    def result(self):
        return mock.create_autospec(Result)

    @pytest.fixture
    def window(self):
        return UlauncherWindow()

    def test_create_item_widgets(self, window, result, GtkBuilder):
        assert window.create_item_widgets([result], 'test') == [GtkBuilder.return_value.get_object.return_value]
        GtkBuilder.return_value.get_object.assert_called_with('item-frame')
        GtkBuilder.return_value.get_object.return_value.initialize.assert_called_with(
            GtkBuilder.return_value, result, 0, 'test')
