from __future__ import annotations

import logging
from typing import Callable, Iterator

from ulauncher.internals import actions
from ulauncher.internals.actions import ActionMessage
from ulauncher.internals.query import Query
from ulauncher.internals.result import KeywordTrigger, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.shortcuts.results import ShortcutResult, ShortcutStaticTrigger
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb

logger = logging.getLogger()


def get_description(shortcut: Shortcut, query: Query | None = None) -> str:
    description = "" if shortcut.cmd.startswith("#!") else shortcut.cmd
    if query and query.keyword == shortcut.keyword:
        if not query.argument:
            return "Type in your query and press Enter..."
        return description.replace("%s", query.argument)
    return description.replace("%s", str(query) if query else "...")


def convert_to_result(shortcut: Shortcut, query: Query | None = None) -> ShortcutResult:
    return ShortcutResult(**shortcut, description=get_description(shortcut, query))


class ShortcutMode(BaseMode):
    shortcuts_db: dict[str, Shortcut]

    def __init__(self) -> None:
        self.shortcuts_db = ShortcutsDb.load()

    def _get_active_shortcut(self, query: Query) -> Shortcut | None:
        for s in self.shortcuts_db.values():
            if query.keyword == s.keyword and (query.is_active or s.run_without_argument):
                return s

        return None

    def handle_query(self, query: Query, callback: Callable[[ActionMessage | list[Result]], None]) -> None:
        shortcut = self._get_active_shortcut(query)
        if not shortcut:
            msg = "Query doesn't match any shortcut"
            raise RuntimeError(msg)

        callback([convert_to_result(shortcut, query)])

    def get_fallback_results(self, query_str: str) -> list[ShortcutResult]:
        query = Query(None, query_str)
        return [convert_to_result(s, query) for s in self.shortcuts_db.values() if s["is_default_search"]]

    def get_triggers(self) -> Iterator[Result]:
        for shortcut in self.shortcuts_db.values():
            yield (
                ShortcutStaticTrigger(**shortcut, description=get_description(shortcut))
                if shortcut.run_without_argument
                else KeywordTrigger(**shortcut, description=get_description(shortcut))
            )

    def activate_result(
        self, result: Result, query: Query, _alt: bool, callback: Callable[[ActionMessage | list[Result]], None]
    ) -> None:
        if isinstance(result, ShortcutStaticTrigger):
            callback(run_shortcut(result.cmd))
            return
        if isinstance(result, ShortcutResult):
            argument = query.argument or "" if query.keyword == result.keyword else str(query)
            if argument or not result.keyword:
                callback(run_shortcut(result.cmd, argument or None))
                return
            callback(actions.do_nothing())
            return
        logger.error("Unexpected result type for Shortcut mode '%s'", result)
        callback(actions.do_nothing())
