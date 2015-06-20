import pytest
from ulauncher.search.web.WebResultItem import WebResultItem
from ulauncher.ext.Query import Query


class TestWebResultItem:

    @pytest.fixture
    def ActionList(self, mocker):
        return mocker.patch('ulauncher.search.web.WebResultItem.ActionList')

    @pytest.fixture
    def OpenUrlAction(self, mocker):
        return mocker.patch('ulauncher.search.web.WebResultItem.OpenUrlAction')

    @pytest.fixture
    def SetUserQueryAction(self, mocker):
        return mocker.patch('ulauncher.search.web.WebResultItem.SetUserQueryAction')

    @pytest.fixture
    def item(self):
        return WebResultItem('kw', 'name', 'descr {query}', 'url=%s', 'icon_path')

    def test_get_keyword(self, item):
        assert item.get_keyword() == 'kw'

    def test_get_name(self, item):
        assert item.get_name() == 'name'

    def test_get_description(self, item):
        assert item.get_description(Query('kw test')) == 'descr test'
        assert item.get_description(Query('keyword test')) == 'descr ...'
        assert item.get_description(Query('goo')) == 'descr ...'
        item.set_default_search(True)
        assert item.get_description(Query('kw test')) == 'descr kw test'

    def test_get_icon(self, mocker, item):
        load_image = mocker.patch('ulauncher.search.web.WebResultItem.load_image')
        assert item.get_icon() is load_image.return_value
        load_image.assert_called_once_with('icon_path', 40)

    def test_on_enter(self, item, mocker, ActionList, OpenUrlAction, SetUserQueryAction):
        assert item.on_enter(Query('kw test')) is ActionList.return_value
        OpenUrlAction.assert_called_once_with('url=test')
        assert not SetUserQueryAction.called

    def test_on_enter__default_search(self, item, mocker, ActionList, OpenUrlAction, SetUserQueryAction):
        item.set_default_search(True)
        assert item.on_enter(Query('search query')) is ActionList.return_value
        OpenUrlAction.assert_called_once_with('url=search query')
        assert not SetUserQueryAction.called

    def test_on_enter__misspelled_kw(self, item, mocker, ActionList, OpenUrlAction, SetUserQueryAction):
        assert item.on_enter(Query('keyword query')) is ActionList.return_value
        assert not OpenUrlAction.called
        SetUserQueryAction.assert_called_once_with('kw ')
