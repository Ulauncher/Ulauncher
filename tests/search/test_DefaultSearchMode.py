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

    @pytest.fixture
    def GoogleItem(self, mocker):
        return mocker.patch('ulauncher.search.DefaultSearchMode.GoogleResultItem')

    @pytest.fixture
    def search_mode(self, GoogleItem):
        return DefaultSearchMode()

    def test_on_query(self, search_mode, AppDb, Render, ActionList, SearchMode):
        query = Query('search')
        find = [1]
        AppDb.get_instance.return_value.find.return_value = find
        assert search_mode.on_query(query) == ActionList.return_value
        AppDb.get_instance.return_value.find.assert_called_with(query)
        Render.assert_called_with(find)

    def test_on_query__keyword(self, GoogleItem, search_mode, AppDb, Render, ActionList, SearchMode):
        query = Query('google search')
        GoogleItem.return_value.get_keyword.return_value = 'google'
        assert search_mode.on_query(query) == ActionList.return_value
        Render.assert_called_with((GoogleItem.return_value,))

    def test_on_query__default_search(self, GoogleItem, search_mode, AppDb, Render, ActionList, SearchMode):
        query = Query('search')
        AppDb.get_instance.return_value.find.return_value = []
        assert search_mode.on_query(query) == ActionList.return_value
        assert Render.called
        ActionList.assert_called_with((Render.return_value,))
        GoogleItem.return_value.set_default_search.assert_called_with(True)
