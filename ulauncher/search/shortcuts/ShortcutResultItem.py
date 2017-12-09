import re

from ulauncher.api.shared.action.ActionList import ActionList
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.util.image_loader import load_image
from ulauncher.config import get_data_file


class ShortcutResultItem(ResultItem):

    def __init__(self, keyword, name, cmd, icon, default_search=False, **kw):
        self.keyword = keyword
        self.name = name
        self.cmd = cmd
        self.icon = icon
        self.is_default_search = default_search

    def get_keyword(self):
        return self.keyword

    def get_name(self):
        return self.name

    def get_name_highlighted(self, query, color):
        # highlight only if we did not enter Web search item keyword
        if query.get_keyword() == self.keyword and query.get_argument():
            return
        else:
            return super(ShortcutResultItem, self).get_name_highlighted(query, color)

    def get_description(self, query):
        if self.cmd.startswith('#!'):
            # this is a script
            description = ''
        else:
            description = self.cmd

        if self.is_default_search:
            return description.replace('%s', query)
        elif query.get_keyword() == self.keyword and query.get_argument():
            return description.replace('%s', query.get_argument())
        elif query.get_keyword() == self.keyword and not query.get_argument():
            return 'Type in your query and press Enter...'
        else:
            return description.replace('%s', '...')

    def get_icon(self):
        if self.icon:
            return load_image(self.icon, self.ICON_SIZE)

        return load_image(get_data_file('media', 'executable-icon.png'), self.ICON_SIZE)

    def on_enter(self, query):
        action_list = ActionList()
        if query.get_keyword() == self.keyword and query.get_argument():
            argument = query.get_argument()
        elif self.is_default_search:
            argument = query
        else:
            argument = None

        if argument:

            if re.match(r'^http(s)?://', self.cmd.strip()):
                command = self.cmd.strip().replace('%s', argument)
                action = OpenUrlAction(command)
            else:
                action = RunScriptAction(self.cmd, argument)

            action_list.append(action)
        else:
            action_list.append(SetUserQueryAction('%s ' % self.keyword))

        return action_list
