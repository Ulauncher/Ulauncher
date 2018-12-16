import mock
import pytest
from ulauncher.search.apps.AppResultItem import AppResultItem
from ulauncher.search.apps.AppQueryDb import AppQueryDb
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
    def app_queries(self, mocker):
        get_instance = mocker.patch('ulauncher.search.apps.AppResultItem.AppQueryDb.get_instance')
        get_instance.return_value = mock.create_autospec(AppQueryDb)
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

    def test_selected_by_default(self, item, app_queries):
        app_queries.find.return_value = 'TestAppResultItem'
        assert item.selected_by_default('q')
        app_queries.find.assert_called_with('q')

    def test_on_enter(self, item, mocker, app_queries, app_stat_db):
        LaunchAppAction = mocker.patch('ulauncher.search.apps.AppResultItem.LaunchAppAction')
        assert item.on_enter(Query('query')) is LaunchAppAction.return_value
        LaunchAppAction.assert_called_with('path/to/desktop_file.desktop')
        app_queries.put.assert_called_with('query', 'TestAppResultItem')
        app_queries.commit.assert_called_with()
        app_stat_db.inc_count.assert_called_with('path/to/desktop_file.desktop')
