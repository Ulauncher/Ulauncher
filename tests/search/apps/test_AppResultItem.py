import mock
import pytest
from ulauncher.search.apps.AppResultItem import AppResultItem
from ulauncher.ext.Query import Query


class TestAppResultItem:

    @pytest.fixture
    def item(self):
        return AppResultItem({
            'name': 'TestAppResultItem',
            'description': 'Description of TestAppResultItem',
            'icon': 'icon123',
            'desktop_file': 'path/to/desktop_file.desktop'
        })

    def test_get_name(self, item):
        assert item.get_name() == 'TestAppResultItem'

    def test_get_description(self, item):
        assert item.get_description(Query('q')) == 'Description of TestAppResultItem'

    def test_get_icon(self, item):
        assert item.get_icon() == 'icon123'

    def test_on_enter(self, item, mocker):
        LaunchAppAction = mocker.patch('ulauncher.search.apps.AppResultItem.LaunchAppAction')
        ActionList = mocker.patch('ulauncher.search.apps.AppResultItem.ActionList')
        assert item.on_enter(Query('query')) is ActionList.return_value
        LaunchAppAction.assert_called_with('path/to/desktop_file.desktop')
        ActionList.assert_called_with((LaunchAppAction.return_value,))
