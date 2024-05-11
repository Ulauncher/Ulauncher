import pytest

from ulauncher.modes.shortcuts.shortcut_mode import ShortcutMode
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut as ShortcutRecord


class TestShortcutMode:
    @pytest.fixture
    def mode(self):
        return ShortcutMode()

    @pytest.fixture(autouse=True)
    def shortcuts_db(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_mode.ShortcutsDb.load").return_value

    @pytest.fixture(autouse=True)
    def shortcut_result(self, mocker):
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_mode.ShortcutResult")

    def test_is_enabled__query_starts_with_query_and_space__returns_true(self, mode, shortcuts_db):
        query = "kw "
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert mode.is_enabled(query)

    def test_is_enabled__query_starts_with_query__returns_false(self, mode, shortcuts_db):
        query = "kw"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert not mode.is_enabled(query)

    def test_is_enabled__query_doesnt_start_with_query__returns_false(self, mode, shortcuts_db):
        query = "wk something"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert not mode.is_enabled(query)

    def test_is_enabled__query_run_without_argument__returns_true(self, mode, shortcuts_db):
        query = "wk"
        shortcut = ShortcutRecord(keyword="wk", run_without_argument=True)
        shortcuts_db.values.return_value = [shortcut]

        assert mode.is_enabled(query)

    def test_handle_query__return_value__is(self, mode, shortcuts_db, shortcut_result):
        query = "kw something"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert mode.handle_query(query)[0] == shortcut_result.return_value

    def test_handle_query__shortcut_result__is_called(self, mode, shortcuts_db, shortcut_result):
        query = "kw something"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        mode.handle_query(query)

        shortcut_result.assert_called_once_with(**shortcut)

    def test_get_default_items__shortcut_results__returned(self, mode, shortcuts_db, shortcut_result):
        shortcut = ShortcutRecord(keyword="kw", is_default_search=True)
        shortcuts_db.values.return_value = [shortcut]

        assert mode.get_fallback_results() == [shortcut_result.return_value]

    def test_get_triggers(self, mode, shortcuts_db, shortcut_result):
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]
        assert mode.get_triggers() == [shortcut_result.return_value]
        shortcut_result.assert_called_once_with(**shortcut)
