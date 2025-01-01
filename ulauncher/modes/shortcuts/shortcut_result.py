from __future__ import annotations

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut


class ShortcutResult(Result):
    searchable = True
    run_without_argument = False
    is_default_search = False
    cmd = ""

    def get_highlightable_input(self, query: Query) -> str | None:
        return str(query) if self.keyword != query.keyword else None

    def get_description(self, query: Query) -> str:
        description = "" if self.cmd.startswith("#!") else self.cmd

        if self.run_without_argument:
            return "Press Enter to run the shortcut"

        if query.keyword == self.keyword:
            if not query.argument:
                return "Type in your query and press Enter..."
            return description.replace("%s", query.argument)

        if self.is_default_search:
            return description.replace("%s", query)

        return description.replace("%s", "...")

    def on_activation(self, query: Query, _alt: bool = False) -> bool | str | dict[str, str]:
        if query.keyword == self.keyword and query.argument:
            argument = query.argument
        elif self.is_default_search:
            argument = str(query)
        else:
            argument = ""

        if self.run_without_argument or not argument:
            return run_shortcut(self.cmd)

        if argument:
            return run_shortcut(self.cmd, argument)

        return f"{self.keyword} "
