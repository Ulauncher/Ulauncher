import re

from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.query import Query


class ShortcutResult(Result):
    searchable = True

    # pylint: disable=super-init-not-called, too-many-arguments
    def __init__(self, keyword, name, cmd, icon, default_search=False, run_without_argument=False, **kw):
        self.keyword = keyword
        self.name = name
        self.cmd = cmd
        self.icon = icon
        self.is_default_search = default_search
        self.run_without_argument = run_without_argument

    def get_highlightable_input(self, query: Query):
        return str(query) if self.keyword != query.keyword else None

    def get_description(self, query):
        if self.cmd.startswith("#!"):
            # this is a script
            description = ""
        else:
            description = self.cmd

        if self.is_default_search:
            return description.replace("%s", query)

        if query.keyword == self.keyword and query.argument:
            return description.replace("%s", query.argument)
        if query.keyword == self.keyword and self.run_without_argument:
            return "Press Enter to run the shortcut"
        if query.keyword == self.keyword and not query.argument:
            return "Type in your query and press Enter..."

        return description.replace("%s", "...")

    def on_enter(self, query):
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
            return OpenAction(command) if self._is_url() else RunScriptAction(command, argument)

        return SetUserQueryAction(f"{self.keyword} ")

    def _is_url(self) -> bool:
        return bool(re.match(r"^http(s)?://", self.cmd.strip()))
