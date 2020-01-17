import pytest
import mock

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow


class TestUlauncherWindow:

    @pytest.fixture(autouse=True)
    def init_styles(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow.init_styles')

    @pytest.fixture(autouse=True)
    def Theme(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Theme')

    @pytest.fixture(autouse=True)
    def load_available_themes(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.load_available_themes')

    @pytest.fixture(autouse=True)
    def get_monitor_scale_factor(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.get_monitor_scale_factor')

    @pytest.fixture(autouse=True)
    def cairo_surface_create_from_pixbuf(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Gdk.cairo_surface_create_from_pixbuf')

    @pytest.fixture(autouse=True)
    def new_image_from_surface(self, mocker):
        mocked = mocker.patch('ulauncher.ui.windows.UlauncherWindow.Gtk.Image.new_from_surface')
        mocked.return_value = Gtk.Image()
        return mocked

    @pytest.fixture(autouse=True)
    def load_image(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.load_image')

    @pytest.fixture(autouse=True)
    def start_sync(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.start_app_watcher')

    @pytest.fixture(autouse=True)
    def show_notification(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.show_notification')

    @pytest.fixture(autouse=True)
    def app_cache_db(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.AppCacheDb.get_instance').return_value

    @pytest.fixture(autouse=True)
    def app_stat_db(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.AppStatDb.get_instance').return_value

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Settings.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extDownloader(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.ExtensionDownloader.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extRunner(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.ExtensionRunner.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extServer(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.ExtensionServer.get_instance').return_value

    @pytest.fixture(autouse=True)
    def get_scr_geometry(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.get_current_screen_geometry')

    @pytest.fixture(autouse=True)
    def Keybinder(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Keybinder')

    @pytest.fixture
    def GtkBuilder(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.Gtk').Builder

    @pytest.fixture
    def result_item(self):
        return mock.create_autospec(ResultItem)

    @pytest.fixture(autouse=True)
    def os_path_exists(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.os.path.exists')

    @pytest.fixture(autouse=True)
    def get_data_file(self, mocker):
        return mocker.patch('ulauncher.ui.windows.UlauncherWindow.get_data_file')

    @pytest.fixture
    def window(self):
        return UlauncherWindow()

    @pytest.mark.with_display
    def test_bind_show_app_hotkey(self, window, Keybinder, show_notification, app_cache_db):
        app_cache_db.find.return_value = False
        accel_name = '<Primary><Alt>f'
        window.bind_show_app_hotkey(accel_name)
        Keybinder.bind.assert_called_with(accel_name, window.toggle_window)

        # bind another one
        # this time Ulauncher should unbind previous key
        new_accel_name = '<Primary><Alt>r'
        window.bind_show_app_hotkey(new_accel_name)
        Keybinder.unbind.assert_called_with(accel_name)
        Keybinder.bind.assert_called_with(new_accel_name, window.toggle_window)
        show_notification.assert_called_with('Ulauncher', 'Hotkey is set to Ctrl+Alt+R')

    def test_create_item_widgets(self, window, result_item, GtkBuilder, get_data_file):
        assert window.create_item_widgets([result_item], 'test') == [GtkBuilder.return_value.get_object.return_value]
        GtkBuilder.return_value.get_object.assert_called_with('item-frame')
        GtkBuilder.return_value.get_object.return_value.initialize.assert_called_with(
            GtkBuilder.return_value, result_item, 0, 'test')
        GtkBuilder.return_value.add_from_file.assert_called_with(get_data_file.return_value)
        get_data_file.assert_called_with('ui', '%s.ui' % result_item.UI_FILE)
