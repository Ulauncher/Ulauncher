import pytest
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode


class TestShortcutMode:

    @pytest.fixture
    def mode(self):
        return ShortcutMode()

    @pytest.fixture(autouse=True)
    def shortcuts_db(self, mocker):
        return mocker.patch('ulauncher.modes.shortcuts.ShortcutMode.ShortcutsDb.get_instance').return_value

    @pytest.fixture(autouse=True)
    def ShortcutResult(self, mocker):
        return mocker.patch('ulauncher.modes.shortcuts.ShortcutMode.ShortcutResult')

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

    def test_handle_query__return_value__is(self, mode, shortcuts_db, ShortcutResult):
        query = 'kw something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.handle_query(query)[0] == ShortcutResult.return_value

    def test_handle_query__ShortcutResult__is_called(self, mode, shortcuts_db, ShortcutResult):
        query = 'kw something'
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        mode.handle_query(query)

        ShortcutResult.assert_called_once_with(keyword='kw')

    def test_get_default_items__ShortcutResults__returned(self, mode, shortcuts_db, ShortcutResult):
        shortcut = {'keyword': 'kw', 'is_default_search': True}
        shortcuts_db.get_shortcuts.return_value = [shortcut]

        assert mode.get_default_items() == [ShortcutResult.return_value]

    def test_get_searchable_items(self, mode, shortcuts_db, ShortcutResult):
        shortcut = {'keyword': 'kw'}
        shortcuts_db.get_shortcuts.return_value = [shortcut]
        assert mode.get_searchable_items() == [ShortcutResult.return_value]
        ShortcutResult.assert_called_once_with(default_search=False, **shortcut)
