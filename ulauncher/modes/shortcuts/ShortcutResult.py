import re

from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.query import Query
from ulauncher.modes.shortcuts.run_script import run_script


class ShortcutResult(Result):
    searchable = True
    run_without_argument = False
    is_default_search = False
    cmd = ""

    def get_highlightable_input(self, query: Query):
        return str(query) if self.keyword != query.keyword else None

    def get_description(self, query):
        description = "" if self.cmd.startswith("#!") else self.cmd

        if self.is_default_search:
            return description.replace("%s", query)

        if query.keyword == self.keyword and query.argument:
            return description.replace("%s", query.argument)
        if query.keyword == self.keyword and self.run_without_argument:
            return "Press Enter to run the shortcut"
        if query.keyword == self.keyword and not query.argument:
            return "Type in your query and press Enter..."

        return description.replace("%s", "...")

    def on_activation(self, query, _alt=False):
        if query.keyword == self.keyword and query.argument:
            argument = query.argument
        elif self.is_default_search:
            argument = query
        else:
            argument = None

        command = self.cmd.strip()
        if argument and not self.run_without_argument:
            command = command.replace("%s", argument)

        if argument or self.run_without_argument:
            if self._is_url():
                return OpenAction(command)
            run_script(command, argument)
            return False

        return f"{self.keyword} "

    def _is_url(self) -> bool:
        return bool(re.match(r"^http(s)?://", self.cmd.strip()))
