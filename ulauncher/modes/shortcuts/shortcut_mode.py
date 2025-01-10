from __future__ import annotations

from typing import Iterator

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.shortcuts.shortcut_result import ShortcutResult
from ulauncher.modes.shortcuts.shortcut_trigger import ShortcutTrigger
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb


def get_description(shortcut: Shortcut, query: Query | None = None) -> str:
    description = "" if shortcut.cmd.startswith("#!") else shortcut.cmd
    if query and query.keyword == shortcut.keyword:
        if not query.argument:
            return "Type in your query and press Enter..."
        return description.replace("%s", query.argument)
    return description.replace("%s", query or "...")


def convert_to_result(shortcut: Shortcut, query: Query | None = None) -> ShortcutResult:
    return ShortcutResult(**shortcut, description=get_description(shortcut, query))


class ShortcutMode(BaseMode):
    shortcuts_db: dict[str, Shortcut]

    def __init__(self) -> None:
        self.shortcuts_db = ShortcutsDb.load()

    def is_enabled(self, query_str: str) -> bool:
        """
        Return True if mode should be enabled for a query
        """
        return bool(self._get_active_shortcut(query_str))

    def _get_active_shortcut(self, query_str: str) -> Shortcut | None:
        for s in self.shortcuts_db.values():
            if query_str.startswith(f"{s.keyword} ") or (query_str == s.keyword and s.run_without_argument):
                return s

        return None

    def handle_query(self, query_str: str) -> list[ShortcutResult]:
        """
        @return Action object
        """
        shortcut = self._get_active_shortcut(query_str)
        if not shortcut:
            msg = "Query doesn't match any shortcut"
            raise RuntimeError(msg)

        return [convert_to_result(shortcut, Query(query_str))]

    def get_fallback_results(self) -> list[ShortcutResult]:
        return [convert_to_result(s) for s in self.shortcuts_db.values() if s["is_default_search"]]

    def get_triggers(self) -> Iterator[Result]:
        for shortcut in self.shortcuts_db.values():
            yield ShortcutTrigger(**shortcut, description=get_description(shortcut))
