from __future__ import annotations

from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.shortcuts.shortcut_result import ShortcutResult
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb


def convert_to_result(shortcut: Shortcut) -> ShortcutResult:
    return ShortcutResult(**shortcut)


class ShortcutMode(BaseMode):
    shortcuts_db: dict[str, Shortcut]

    def __init__(self) -> None:
        self.shortcuts_db = ShortcutsDb.load()

    def is_enabled(self, query: str) -> bool:
        """
        Return True if mode should be enabled for a query
        """
        return bool(self._get_active_shortcut(query))

    def _get_active_shortcut(self, query: str) -> Shortcut | None:
        for s in self.shortcuts_db.values():
            if query.startswith(f"{s.keyword} ") or (query == s.keyword and s.run_without_argument):
                return s

        return None

    def handle_query(self, query: str) -> list[ShortcutResult]:
        """
        @return Action object
        """
        shortcut = self._get_active_shortcut(query)
        if not shortcut:
            msg = "Query doesn't match any shortcut"
            raise RuntimeError(msg)

        return [convert_to_result(shortcut)]

    def get_fallback_results(self) -> list[ShortcutResult]:
        return [convert_to_result(s) for s in self.shortcuts_db.values() if s["is_default_search"]]

    def get_triggers(self) -> list[ShortcutResult]:
        return [convert_to_result(s) for s in self.shortcuts_db.values()]
