from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.results import ShortcutResult, ShortcutStaticTrigger
from ulauncher.modes.shortcuts.shortcut_mode import ShortcutMode
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut as ShortcutRecord


def get_results(mode: ShortcutMode, query: Query) -> list[Result]:
    """Helper to collect results from callback-based handle_query."""
    results = []
    mode.handle_query(query, results.extend)
    return results


class TestShortcutMode:
    @pytest.fixture
    def mode(self) -> ShortcutMode:
        return ShortcutMode()

    @pytest.fixture(autouse=True)
    def shortcuts_db(self, mocker: MockerFixture) -> Any:
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_mode.ShortcutsDb.load").return_value

    @pytest.fixture(autouse=True)
    def run_shortcut(self, mocker: MockerFixture) -> Any:
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_mode.run_shortcut")

    @pytest.fixture(autouse=False)
    def shortcut_result(self, mocker: MockerFixture) -> Any:
        return mocker.patch("ulauncher.modes.shortcuts.shortcut_mode.results.ShortcutResult")

    def test_is_enabled__query_starts_with_query__returns_false(
        self, mode: ShortcutMode, shortcuts_db: MagicMock
    ) -> None:
        query = "kw"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert not mode.matches_query_str(query)

    def test_is_enabled__query_doesnt_start_with_query__returns_false(
        self, mode: ShortcutMode, shortcuts_db: MagicMock
    ) -> None:
        query = "wk something"
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert not mode.matches_query_str(query)

    def test_handle_query__return_value__is(
        self, mode: ShortcutMode, shortcuts_db: MagicMock, shortcut_result: ShortcutResult
    ) -> None:
        query = Query("kw", "something")
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        assert get_results(mode, query)[0] == shortcut_result.return_value

    def test_handle_query__shortcut_result__is_called(
        self, mode: ShortcutMode, shortcuts_db: MagicMock, shortcut_result: ShortcutResult
    ) -> None:
        query = Query("kw", "something")
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]

        get_results(mode, query)

        shortcut_result.assert_called_once_with(**shortcut, description="")

    def test_get_default_items__shortcut_results__returned(
        self, mode: ShortcutMode, shortcuts_db: MagicMock, shortcut_result: ShortcutResult
    ) -> None:
        shortcut = ShortcutRecord(keyword="kw", is_default_search=True)
        shortcuts_db.values.return_value = [shortcut]

        assert mode.get_fallback_results("") == [shortcut_result.return_value]

    def test_get_triggers(self, mode: ShortcutMode, shortcuts_db: MagicMock) -> None:
        shortcut = ShortcutRecord(keyword="kw")
        shortcuts_db.values.return_value = [shortcut]
        assert next(mode.get_triggers()).keyword == "kw"

    def test_activate_static_trigger(self, mode: ShortcutMode, run_shortcut: MagicMock) -> None:
        query = Query("kw", None)
        result = ShortcutStaticTrigger(cmd="/bin/asdf", run_without_argument=True)
        mode.activate_result("run_static", result, query, lambda _: None)
        run_shortcut.assert_called_once_with("/bin/asdf")

    def test_activate_shortcutresult_cmd(self, mode: ShortcutMode, run_shortcut: MagicMock) -> None:
        query = Query("kw", "arg")
        result = ShortcutResult(keyword="kw", cmd="/bin/asdf")
        mode.activate_result("run", result, query, lambda _: None)
        run_shortcut.assert_called_once_with("/bin/asdf", "arg")

    def test_activate_shortcutresult_cmd_missing_arg(self, mode: ShortcutMode, run_shortcut: MagicMock) -> None:
        query = Query("kw", None)
        result = ShortcutResult(keyword="kw", cmd="/bin/asdf")
        mode.activate_result("run", result, query, lambda _: None)
        run_shortcut.assert_not_called()

    def test_activate_shortcutresult_run_without_args_no_op(self, mode: ShortcutMode, run_shortcut: MagicMock) -> None:
        # "run without args" are used for to define custom launch scripts etc. they should have no keyword
        # it would be weird if typing without pressing enter would run a command
        query = Query("kw", None)
        result = ShortcutResult(keyword="kw", cmd="/bin/asdf", run_without_argument=True)
        mode.activate_result("run", result, query, lambda _: None)
        run_shortcut.assert_not_called()
