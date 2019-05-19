import pytest
from ulauncher.search.shortcuts.ShortcutSearchMode import ShortcutSearchMode


class TestShortcutSearchMode:

    @pytest.fixture
    def mode(self):
        return ShortcutSearchMode()

    @pytest.fixture(autouse=True)
    def shortcuts_db(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutSearchMode.ShortcutsDb.get_instance').return_value

    @pytest.fixture(autouse=True)
    def RenderAction(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutSearchMode.RenderResultListAction')

    @pytest.fixture(autouse=True)
    def ShortcutResultItem(self, mocker):
        return mocker.patch('ulauncher.search.shortcuts.ShortcutSearchMode.ShortcutResultItem')

    def test_is_enabled__query_starts_with_query_and_space__returns_true(self, mode, shortcuts_db):
        query = 'kw '
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.is_enabled(query)

    def test_is_enabled__query_starts_with_query__returns_false(self, mode, shortcuts_db):
        query = 'kw'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert not mode.is_enabled(query)

    def test_is_enabled__query_doesnt_start_with_query__returns_false(self, mode, shortcuts_db):
        query = 'wk something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert not mode.is_enabled(query)

    def test_is_enabled__query_run_without_argument__returns_true(self, mode, shortcuts_db):
        query = 'wk'
        shortcut = {'keyword': 'wk', 'run_without_argument': True}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.is_enabled(query)

    def test_handle_query__return_value__is_RenderAction_object(self, mode, shortcuts_db, RenderAction):
        query = 'kw something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.handle_query(query) == RenderAction.return_value

    def test_handle_query__ShortcutResultItem__is_called(self, mode, shortcuts_db, ShortcutResultItem):
        query = 'kw something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        mode.handle_query(query)

        ShortcutResultItem.assert_called_once_with(keyword='kw')

    def test_handle_query__RenderAction__is_called(self, mode, shortcuts_db, RenderAction, ShortcutResultItem):
        query = 'kw something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        mode.handle_query(query)

        RenderAction.assert_called_once_with([ShortcutResultItem.return_value])

    def test_get_default_items__ShortcutResultItems__returned(self, mode, shortcuts_db, ShortcutResultItem):
        shortcut = {'keyword': 'kw', 'is_default_search': True}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.get_default_items() == [ShortcutResultItem.return_value]

    def test_get_searchable_items(self, mode, shortcuts_db, ShortcutResultItem):
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]
        assert mode.get_searchable_items() == [ShortcutResultItem.return_value]
        ShortcutResultItem.assert_called_once_with(default_search=False, **shortcut)
