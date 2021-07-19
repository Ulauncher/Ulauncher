import re

from ulauncher.api.shared.action.ActionList import ActionList
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.utils.image_loader import load_image
from ulauncher.config import get_data_file
from ulauncher.search.QueryHistoryDb import QueryHistoryDb


class ShortcutResultItem(ResultItem):

    # pylint: disable=super-init-not-called, too-many-arguments
    def __init__(self, keyword, name, cmd, icon, default_search=False, run_without_argument=False, **kw):
        self.keyword = keyword
        self.name = name
        self.cmd = cmd
        self.icon = icon
        self.is_default_search = default_search
        self.run_without_argument = run_without_argument
        self._query_history = QueryHistoryDb.get_instance()

    def get_keyword(self):
        return self.keyword

    def get_name(self):
        return self.name

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

    def get_icon(self):
        if self.icon:
            return load_image(self.icon, self.get_icon_size())

        return load_image(get_data_file('media', 'executable-icon.png'), self.get_icon_size())

    def selected_by_default(self, query):
        """
        :param ~ulauncher.search.Query.Query query:
        """
        return self._query_history.find(query) == self.get_name()

    def on_enter(self, query):
        action_list = ActionList()
        if query.get_keyword() == self.keyword and query.get_argument():
            argument = query.get_argument()
        elif self.is_default_search:
            argument = query
        else:
            argument = None

        if self.run_without_argument:
            if self._is_url():
                action = OpenUrlAction(self.cmd.strip())
            else:
                action = RunScriptAction(self.cmd)
            action_list.append(action)
        elif argument:
            if self._is_url():
                command = self.cmd.strip().replace('%s', argument)
                action = OpenUrlAction(command)
            else:
                action = RunScriptAction(self.cmd, argument)
            action_list.append(action)
        else:
            action_list.append(SetUserQueryAction('%s ' % self.keyword))

        self._query_history.save_query(query, self.get_name())

        return action_list

    def _is_url(self) -> bool:
        return bool(re.match(r'^http(s)?://', self.cmd.strip()))
