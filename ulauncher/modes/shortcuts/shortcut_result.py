from __future__ import annotations

import re

from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.modes.shortcuts.shortcuts_db import ShortcutsDb


class ShortcutResult(Result):
    searchable = True
    run_without_argument = False
    is_default_search = False
    cmd = ""
    _shortcuts_db = None

    @classmethod
    def get_shortcuts_db(cls) -> ShortcutsDb:
        if cls._shortcuts_db is None:
            cls._shortcuts_db = ShortcutsDb.load()
        return cls._shortcuts_db

    def get_highlightable_input(self, query: Query) -> str | None:
        return str(query) if self.keyword != query.keyword else None

    def get_description(self, query: Query) -> str:
        description = "" if self.cmd.startswith("#!") else self.cmd
        if self.run_without_argument:
            return "Press Enter to run the shortcut"

        shortcuts_db = self.get_shortcuts_db()
        if self.is_default_search and not shortcuts_db.contains_keyword(query.keyword):
            return description.replace("%s", query)

        if query.keyword == self.keyword and query.argument:
            return description.replace("%s", query.argument)
        if query.keyword == self.keyword and not query.argument:
            return "Type in your query and press Enter..."

        return description.replace("%s", "...")

    def on_activation(self, query: Query, _alt: bool = False) -> bool | str | dict[str, str]:
        if query.keyword == self.keyword and query.argument:
            argument = query.argument
        elif self.is_default_search:
            argument = str(query)
        else:
            argument = ""

        command = self.cmd.strip()
        if argument and not self.run_without_argument:
            command = command.replace("%s", argument)

        if argument or self.run_without_argument:
            if self._is_url():
                return actions.open(command)
            run_script(command, argument)
            return False

        return f"{self.keyword} "

    def _is_url(self) -> bool:
        return bool(re.match(r"^http(s)?://", self.cmd.strip()))
