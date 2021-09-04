import pytest
from ulauncher.search.shortcuts.ShortcutResultItem import ShortcutResultItem
from ulauncher.search.Query import Query


class TestShortcutResultItem:

    @pytest.fixture
    def ActionList(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.ActionList')

    @pytest.fixture(autouse=True)
    def OpenUrlAction(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.OpenUrlAction')

    @pytest.fixture(autouse=True)
    def RunScriptAction(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.RunScriptAction')

    @pytest.fixture(autouse=True)
    def query_history(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.QueryHistoryDb.get_instance').return_value

    @pytest.fixture
    def SetUserQueryAction(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.SetUserQueryAction')

    @pytest.fixture
    def item(self):
        return ShortcutResultItem('kw', 'name', 'https://site/?q=%s', 'icon_path',
                                  is_default_search=True, run_without_argument=False)

    def test_get_keyword(self, item):
        assert item.get_keyword() == 'kw'

    def test_get_name(self, item):
        assert item.get_name() == 'name'

    def test_get_description(self, item):
        assert item.get_description(Query('kw test')) == 'https://site/?q=test'
        assert item.get_description(Query('keyword test')) == 'https://site/?q=...'
        assert item.get_description(Query('goo')) == 'https://site/?q=...'

    def test_get_icon(self, mocker, item):
        load_image = mocker.patch('ulauncher.search.shortcuts.ShortcutResultItem.load_image')
        assert item.get_icon() is load_image.return_value
        load_image.assert_called_once_with('icon_path', 40)

    def test_on_enter(self, item, ActionList, OpenUrlAction, SetUserQueryAction):
        assert item.on_enter(Query('kw test')) is ActionList.return_value
        OpenUrlAction.assert_called_once_with('https://site/?q=test')
        assert not SetUserQueryAction.called

    def test_on_enter__default_search(self, item, ActionList, OpenUrlAction, SetUserQueryAction):
        item.is_default_search = True
        assert item.on_enter(Query('search query')) is ActionList.return_value
        OpenUrlAction.assert_called_once_with('https://site/?q=search query')
        assert not SetUserQueryAction.called

    def test_on_enter__run_without_arguments(self, item, ActionList, OpenUrlAction, SetUserQueryAction):
        item.run_without_argument = True
        assert item.on_enter(Query('kw')) is ActionList.return_value
        # it doesn't replace %s if run_without_argument = True
        OpenUrlAction.assert_called_once_with('https://site/?q=%s')
        assert not SetUserQueryAction.called

    def test_on_enter__misspelled_kw(self, item, ActionList, OpenUrlAction, SetUserQueryAction):
        assert item.on_enter(Query('keyword query')) is ActionList.return_value
        assert not OpenUrlAction.called
        SetUserQueryAction.assert_called_once_with('kw ')

    def test_on_enter__run_file(self, ActionList, RunScriptAction):
        item = ShortcutResultItem('kw', 'name', '/usr/bin/something', 'icon_path')
        assert item.on_enter(Query('kw query')) is ActionList.return_value
        RunScriptAction.assert_called_once_with('/usr/bin/something', 'query')

    def test_on_enter__save_query_to_history(self, item, query_history):
        item.on_enter(Query('my-query'))
        query_history.save_query.assert_called_once_with('my-query', 'name')
