from __future__ import annotations

from ulauncher.api import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut


class ShortcutTrigger(Result):
    searchable = True
    run_without_argument = False
    cmd = ""

    def on_activation(self, _query: Query, _alt: bool = False) -> bool | str | actions.Action[str]:
        if not self.run_without_argument:
            return f"{self.keyword} "

        return run_shortcut(self.cmd)
