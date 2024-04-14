from __future__ import annotations

from typing import Any

from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.shortcuts.ShortcutResult import ShortcutResult
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb


class ShortcutMode(BaseMode):
    shortcutsDb: dict[str, ShortcutResult]

    def __init__(self) -> None:
        self.shortcutsDb = ShortcutsDb.load()

    def is_enabled(self, query: str) -> bool:
        """
        Return True if mode should be enabled for a query
        """
        return bool(self._get_active_shortcut(query))

    def _get_active_shortcut(self, query: str) -> ShortcutResult | None:
        for s in self.shortcutsDb.values():
            if query.startswith(f"{s.keyword} ") or (query == s.keyword and s.run_without_argument):
                return s

        return None

    def _create_items(self, shortcuts: list[dict[str, Any]]) -> list[ShortcutResult]:
        return [ShortcutResult(**s) for s in shortcuts]

    def handle_query(self, query: str) -> list[ShortcutResult]:
        """
        @return Action object
        """
        shortcut = self._get_active_shortcut(query)
        if not shortcut:
            msg = "Query doesn't match any shortcut"
            raise RuntimeError(msg)

        return [ShortcutResult(**shortcut)]

    def get_fallback_results(self) -> list[ShortcutResult]:
        return self._create_items([s for s in self.shortcutsDb.values() if s["is_default_search"]])

    def get_triggers(self) -> list[ShortcutResult]:
        return self._create_items(list(self.shortcutsDb.values()))
