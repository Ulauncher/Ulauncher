from __future__ import annotations

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut


class ShortcutResult(Result):
    searchable = True
    is_default_search = False
    cmd = ""

    def get_highlightable_input(self, query: Query) -> str | None:
        return str(query) if self.keyword != query.keyword else None

    def on_activation(self, query: Query, _alt: bool = False) -> bool | str | dict[str, str]:
        argument = query.argument or "" if query.keyword == self.keyword else str(query)
        return run_shortcut(self.cmd, argument or None)
