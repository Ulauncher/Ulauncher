import mock
import pytest
from ulauncher.search.apps.AppResultItem import AppResultItem
from ulauncher.search.QueryHistoryDb import QueryHistoryDb
from ulauncher.search.apps.AppStatDb import AppStatDb
from ulauncher.search.Query import Query


class TestAppResultItem:

    @pytest.fixture
    def item(self):
        return AppResultItem({
            'name': 'TestAppResultItem',
            'description': 'Description of TestAppResultItem',
            'icon': 'icon123',
            'desktop_file': 'path/to/desktop_file.desktop'
        })

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

    def test_get_name(self, item):
        assert item.get_name() == 'TestAppResultItem'

    def test_get_description(self, item):
        assert item.get_description(Query('q')) == 'Description of TestAppResultItem'

    def test_get_icon(self, item):
        assert item.get_icon() == 'icon123'

    def test_selected_by_default(self, item, query_history):
        query_history.find.return_value = 'TestAppResultItem'
        assert item.selected_by_default('q')
        query_history.find.assert_called_with('q')

    def test_on_enter(self, item, mocker, query_history, app_stat_db):
        LaunchAppAction = mocker.patch('ulauncher.search.apps.AppResultItem.LaunchAppAction')
        assert item.on_enter(Query('query')) is LaunchAppAction.return_value
        LaunchAppAction.assert_called_with('path/to/desktop_file.desktop')
        query_history.save_query.assert_called_with('query', 'TestAppResultItem')
        app_stat_db.inc_count.assert_called_with('path/to/desktop_file.desktop')
