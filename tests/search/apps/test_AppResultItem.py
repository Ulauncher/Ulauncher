import pathlib
import mock
import pytest
import gi
gi.require_version('Gio', '2.0')
gi.require_version('GdkPixbuf', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio, GdkPixbuf

from ulauncher.search.apps.AppResultItem import AppResultItem
from ulauncher.search.QueryHistoryDb import QueryHistoryDb
from ulauncher.search.apps.AppStatDb import AppStatDb
from ulauncher.search.Query import Query

# Note: These mock apps actually need real values for Exec or Icon, or they won't load,
# and they need to load from actual files or get_id() and get_filename() will return None
ENTRIES_DIR = pathlib.Path(__file__).parent.joinpath('mock_desktop_entries').resolve()


class TestAppResultItem:

    @pytest.fixture
    def app1(self):
        return AppResultItem(Gio.DesktopAppInfo.new_from_filename(f'{ENTRIES_DIR}/trueapp.desktop'))

    @pytest.fixture
    def app2(self):
        return AppResultItem(Gio.DesktopAppInfo.new_from_filename(f'{ENTRIES_DIR}/falseapp.desktop'))

    @pytest.fixture(autouse=True)
    def query_history(self, mocker):
        get_instance = mocker.patch('ulauncher.search.apps.AppResultItem.QueryHistoryDb.get_instance')
        get_instance.return_value = mock.create_autospec(QueryHistoryDb)
        return get_instance.return_value

    @pytest.fixture(autouse=True)
    def app_stat_db(self, mocker):
        get_instance = mocker.patch('ulauncher.search.apps.AppResultItem.AppStatDb.get_instance')
        get_instance.return_value = mock.create_autospec(AppStatDb)
        return get_instance.return_value

    def test_get_name(self, app1):
        assert app1.get_name() == 'TrueApp - Full Name'

    def test_get_description(self, app1):
        assert app1.get_description(Query('q')) == 'Your own yes-man'

    def test_get_icon(self, app1):
        assert isinstance(app1.get_icon(), GdkPixbuf.Pixbuf)
        assert app1.get('Icon') == 'dialog-yes'

    def test_selected_by_default(self, app1, query_history):
        query_history.find.return_value = 'TrueApp - Full Name'
        assert app1.selected_by_default('q')
        query_history.find.assert_called_with('q')

    def test_on_enter(self, app1, mocker, query_history, app_stat_db):
        LaunchAppAction = mocker.patch('ulauncher.search.apps.AppResultItem.LaunchAppAction')
        assert app1.on_enter(Query('query')) is LaunchAppAction.return_value
        LaunchAppAction.assert_called_with(f'{ENTRIES_DIR}/trueapp.desktop')
        query_history.save_query.assert_called_with('query', 'TrueApp - Full Name')
        app_stat_db.inc_count.assert_called_with('trueapp.desktop')
