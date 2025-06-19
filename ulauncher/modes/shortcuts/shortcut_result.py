from __future__ import annotations

from ulauncher.api import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut


class ShortcutResult(Result):
    searchable = True
    is_default_search = False
    run_without_argument = False
    cmd = ""

    def get_highlightable_input(self, query: Query) -> str | None:
        return str(query) if self.keyword != query.keyword else None

    def on_activation(self, query: Query, _alt: bool = False) -> bool | str | actions.Action[str]:
        argument = query.argument or "" if query.keyword == self.keyword else str(query)
        if argument or self.run_without_argument:
            return run_shortcut(self.cmd, argument or None)
        return True
