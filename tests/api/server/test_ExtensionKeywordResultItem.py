import pytest

from ulauncher.api.server.ExtensionKeywordResultItem import ExtensionKeywordResultItem
from ulauncher.search.Query import Query


class TestExtensionKeywordResultItem:

    @pytest.fixture(autouse=True)
    def query_history(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionKeywordResultItem.QueryHistoryDb.get_instance').return_value

    @pytest.fixture
    def item(self):
        return ExtensionKeywordResultItem('name', 'description', 'kw', 'icon_path')

    def test_selected_by_default__query_in_history__returns_true(self, item, query_history):
        query_history.find.return_value = 'name'
        assert item.selected_by_default(Query('query'))

    def test_selected_by_default__query_not_in_history__returns_true(self, item, query_history):
        query_history.find.return_value = 'name2'
        assert not item.selected_by_default(Query('query'))

    def test_on_enter__save_query_to_history(self, item, query_history):
        item.on_enter(Query('my-query'))
        query_history.save_query.assert_called_once_with('my-query', 'name')
