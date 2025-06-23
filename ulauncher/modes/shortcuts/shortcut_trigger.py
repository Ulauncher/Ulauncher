from __future__ import annotations

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut


class ShortcutTrigger(Result):
    searchable = True
    run_without_argument = False
    cmd = ""

    def on_activation(self, _query: Query, _alt: bool = False) -> ActionMetadata:
        if not self.run_without_argument:
            return f"{self.keyword} "

        return run_shortcut(self.cmd)
