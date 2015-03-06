import pytest
import mock
from gi.repository import Gtk, Gio, GdkPixbuf

mock.patch('ulauncher_lib.helpers.lru_cache', side_effect=lambda fn: fn)

from ulauncher.results.IconLoader import IconLoader, load_icon


@pytest.fixture
def pixbuf_icon():
    pixbuf_icon = mock.create_autospec(GdkPixbuf.Pixbuf)
    return pixbuf_icon


@pytest.fixture
def callback():
    return mock.MagicMock()


@pytest.fixture
def file_icon():
    file_icon = mock.create_autospec(Gio.FileIcon)
    file_icon.get_file = mock.MagicMock()
    return file_icon


@pytest.fixture
def themed_icon():
    themed_icon = mock.create_autospec(Gio.ThemedIcon)
    themed_icon.get_names = mock.MagicMock()
    return themed_icon


class Test_load_icon:

    @pytest.fixture(autouse=True)
    def IconLoader(self, mocker):
        return mocker.patch('ulauncher.results.IconLoader.IconLoader')

    def test_returns_pixbuf_if_passed_pixbuf(self, pixbuf_icon, callback):
        assert load_icon(pixbuf_icon, 40, callback)
        callback.assert_called_with(pixbuf_icon)

    def test_themed_icon(self, themed_icon, callback, IconLoader):
        assert load_icon(themed_icon, 40, callback) == IconLoader.return_value.is_ready.return_value
        IconLoader.assert_called_with(themed_icon.get_names.return_value[0], 40, True)
        IconLoader.return_value.add_callback.assert_called_with(callback)
        IconLoader.return_value.start.assert_called_with()

    def test_file_icon(self, file_icon, callback, IconLoader):
        assert load_icon(file_icon, 40, callback) == IconLoader.return_value.is_ready.return_value
        IconLoader.assert_called_with(file_icon.get_file.return_value.get_path.return_value, 40, False)
        IconLoader.return_value.add_callback.assert_called_with(callback)
        IconLoader.return_value.start.assert_called_with()


class TestIconLoader(object):

    @pytest.fixture(autouse=True)
    def load_icon(self, mocker):
        load_icon = mocker.patch('ulauncher.results.IconLoader.load_icon')
        load_icon.return_value = mock.create_autospec(GdkPixbuf.Pixbuf)
        return load_icon

    @pytest.fixture(autouse=True)
    def Thread(self, mocker):
        return mocker.patch('ulauncher.results.IconLoader.Thread')

    @pytest.fixture
    def loader(self, themed_icon, callback):
        loader = IconLoader(themed_icon, 30, True)
        print type(loader)
        loader.add_callback(callback)
        return loader

    def test_run(self, loader, mocker, callback):
        get_pixbuf = mocker.patch.object(loader, 'get_pixbuf')
        assert not loader.is_started()
        assert not loader.is_ready()
        loader.run()
        assert loader.is_started()
        assert loader.is_ready()
        callback.assert_called_with(get_pixbuf.return_value)

    def test_get_pixbuf(self, loader, mocker):
        load_themed_icon = mocker.patch.object(loader, 'load_themed_icon')
        load_image = mocker.patch('ulauncher.results.IconLoader.load_image')

        loader.get_pixbuf('iconname', 43, True)
        load_themed_icon.assert_called_with('iconname', 43)
        assert not load_image.called

        load_themed_icon.reset_mock()
        load_image.reset_mock()

        loader.get_pixbuf('iconname', 43, False)
        load_image.assert_called_with('iconname', 43)
        assert not load_themed_icon.called

    def test_add_callback(self, loader, callback, mocker):
        mocker.patch.object(loader, 'is_started', return_value=True)
        mocker.patch.object(loader, 'is_ready', return_value=True)
        loader.add_callback(callback)
        loader.start()
        callback.assert_called_with(mock.ANY)

    def test_load_themed_icon(self, loader, themed_icon, mocker):
        icon_theme = mocker.patch('ulauncher.results.IconLoader.icon_theme')
        assert loader.load_themed_icon(themed_icon, 33) == icon_theme.lookup_icon.return_value.load_icon.return_value
        icon_theme.lookup_icon.assert_called_with(themed_icon, 33, mock.ANY)

    def test_load_themed_icon_retuns_None(self, loader, themed_icon, mocker):
        icon_theme = mocker.patch('ulauncher.results.IconLoader.icon_theme')
        icon_theme.lookup_icon.side_effect = Exception
        assert loader.load_themed_icon(themed_icon, 33) is None
        icon_theme.lookup_icon.assert_called_with(themed_icon, 33, mock.ANY)
