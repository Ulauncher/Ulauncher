import os
import re

from ulauncher.api import SearchableResult
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction


class ShortcutResult(SearchableResult):

    # pylint: disable=super-init-not-called, too-many-arguments
    def __init__(self, keyword, name, cmd, icon, default_search=False, run_without_argument=False, **kw):
        self.keyword = keyword
        self.name = name
        self.cmd = cmd
        self.icon = icon and os.path.expanduser(icon)
        self.is_default_search = default_search
        self.run_without_argument = run_without_argument

    def get_name_highlighted(self, query, color):
        # highlight only if we did not enter Web search item keyword
        if query.get_keyword() == self.keyword and query.get_argument():
            return None

        return super().get_name_highlighted(query, color)

    def get_description(self, query):
        if self.cmd.startswith('#!'):
            # this is a script
            description = ''
        else:
            description = self.cmd

        if self.is_default_search:
            return description.replace('%s', query)

        if query.get_keyword() == self.keyword and query.get_argument():
            return description.replace('%s', query.get_argument())
        if query.get_keyword() == self.keyword and self.run_without_argument:
            return 'Press Enter to run the shortcut'
        if query.get_keyword() == self.keyword and not query.get_argument():
            return 'Type in your query and press Enter...'

        return description.replace('%s', '...')

    def on_enter(self, query):
        if query.get_keyword() == self.keyword and query.get_argument():
            argument = query.get_argument()
        elif self.is_default_search:
            argument = query
        else:
            argument = None

        command = self.cmd.strip()
        if argument and not self.run_without_argument:
            command = command.replace('%s', argument)

        if argument or self.run_without_argument:
            return OpenAction(command) if self._is_url() else RunScriptAction(command)

        return SetUserQueryAction(f'{self.keyword} ')

    def _is_url(self) -> bool:
        return bool(re.match(r'^http(s)?://', self.cmd.strip()))
