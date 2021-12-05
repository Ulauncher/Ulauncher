import pathlib
import mock
import pytest
import gi
gi.require_version('Gio', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.modes.apps.AppResultItem import AppResultItem
from ulauncher.modes.QueryHistoryDb import QueryHistoryDb
from ulauncher.modes.Query import Query

# Note: These mock apps actually need real values for Exec or Icon, or they won't load,
# and they need to load from actual files or get_id() and get_filename() will return None
ENTRIES_DIR = pathlib.Path(__file__).parent.joinpath('mock_desktop_entries').resolve()


class TestAppResultItem:
    @pytest.fixture(autouse=True)
    def patch_DesktopAppInfo_new(self, mocker):
        def mkappinfo(app_id):
            return Gio.DesktopAppInfo.new_from_filename(f'{ENTRIES_DIR}/{app_id}')
        return mocker.patch("ulauncher.modes.apps.AppResultItem.Gio.DesktopAppInfo.new", new=mkappinfo)

    @pytest.fixture(autouse=True)
    def patch_DesktopAppInfo_get_all(self, mocker):
        def get_all_appinfo():
            return map(Gio.DesktopAppInfo.new, ['trueapp.desktop', 'falseapp.desktop'])
        return mocker.patch("ulauncher.modes.apps.AppResultItem.Gio.DesktopAppInfo.get_all", new=get_all_appinfo)

    @pytest.fixture
    def app1(self):
        return AppResultItem.from_id('trueapp.desktop')

    @pytest.fixture
    def app2(self):
        return AppResultItem.from_id('falseapp.desktop')

    @pytest.fixture(autouse=True)
    def query_history(self, mocker):
        get_instance = mocker.patch('ulauncher.modes.apps.AppResultItem.QueryHistoryDb.get_instance')
        get_instance.return_value = mock.create_autospec(QueryHistoryDb)
        return get_instance.return_value

    @pytest.fixture(autouse=True)
    def _app_starts(self, mocker):
        db = KeyValueJsonDb('/tmp/mock.json').open()
        db.set_records({'falseapp.desktop': 3000, 'trueapp.desktop': 765})
        return mocker.patch("ulauncher.modes.apps.AppResultItem._app_starts", new=db)

    def test_get_name(self, app1):
        assert app1.get_name() == 'TrueApp - Full Name'

    def test_get_description(self, app1):
        assert app1.get_description(Query('q')) == 'Your own yes-man'

    def test_get_icon(self, app1):
        assert isinstance(app1.get_icon(), str)
        assert app1.get('Icon') == 'dialog-yes'

    def test_search_score(self, app1):
        assert app1.search_score("true") > app1.search_score("trivago")

    def test_search(self):
        searchresults = AppResultItem.search('false', min_score=0)
        assert len(searchresults) == 2
        assert searchresults[0].get_name() == 'FalseApp - Full Name'

    def test_selected_by_default(self, app1, query_history):
        query_history.find.return_value = 'TrueApp - Full Name'
        assert app1.selected_by_default('q')
        query_history.find.assert_called_with('q')

    def test_on_enter(self, app1, mocker, query_history, _app_starts):
        LaunchAppAction = mocker.patch('ulauncher.modes.apps.AppResultItem.LaunchAppAction')
        assert app1.on_enter(Query('query')) is LaunchAppAction.return_value
        LaunchAppAction.assert_called_with(f'{ENTRIES_DIR}/trueapp.desktop')
        query_history.save_query.assert_called_with('query', 'TrueApp - Full Name')
        assert _app_starts._records.get('trueapp.desktop') == 766

    def test_get_most_frequent(self):
        assert len(AppResultItem.get_most_frequent()) == 2
        assert AppResultItem.get_most_frequent()[0].get_name() == 'FalseApp - Full Name'
