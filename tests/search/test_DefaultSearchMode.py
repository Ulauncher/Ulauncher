import mock
import pytest
from ulauncher.search.DefaultSearchMode import DefaultSearchMode
from ulauncher.ext.Query import Query


class TestDefaultSearchMode:

    @pytest.fixture
    def ActionList(self, mocker):
        return mocker.patch('ulauncher.search.DefaultSearchMode.ActionList')

    @pytest.fixture
    def SearchMode(self, mocker):
        return mocker.patch('ulauncher.search.DefaultSearchMode.SearchMode')

    @pytest.fixture
    def Render(self, mocker):
        return mocker.patch('ulauncher.search.DefaultSearchMode.RenderResultListAction')

    @pytest.fixture
    def AppDb(self, mocker):
        return mocker.patch('ulauncher.search.DefaultSearchMode.AppDb')

    @pytest.fixture(autouse=True)
    def ShortcutsDb(self, mocker):
        ShortcutsDb = mocker.patch('ulauncher.search.DefaultSearchMode.ShortcutsDb')
        ShortcutsDb.get_instance.return_value.get_result_items.return_value = []
        return ShortcutsDb.get_instance.return_value

    @pytest.fixture
    def search_mode(self):
        return DefaultSearchMode()

    def test_on_query(self, search_mode, AppDb, Render, ActionList, SearchMode):
        query = Query('search')
        find = [1]
        AppDb.get_instance.return_value.find.return_value = find
        assert search_mode.on_query(query) == ActionList.return_value
        AppDb.get_instance.return_value.find.assert_called_with(query)
        Render.assert_called_with(find)
