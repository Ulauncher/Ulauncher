from ulauncher.ext.ResultItem import ResultItem
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.OpenUrlAction import OpenUrlAction
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.helpers import load_image


class WebResultItem(ResultItem):

    is_default_search = False  # True when no results were found for user's query

    def __init__(self, keyword, name, description, url, icon_path):
        self.keyword = keyword
        self.name = name
        self.description = description
        self.url = url
        self.icon_path = icon_path

    def set_default_search(self, value):
        self.is_default_search = value

    def get_keyword(self):
        return self.keyword

    def get_name(self):
        return self.name

    def get_name_highlighted(serlf, *args):
        pass

    def get_description(self, query):
        if self.is_default_search:
            return self.description.replace('{query}', query)
        elif query.get_keyword() == self.keyword and query.get_argument():
            return self.description.replace('{query}', query.get_argument())
        else:
            return self.description.replace('{query}', '...')

    def get_icon(self):
        return load_image(self.icon_path, self.ICON_SIZE)

    def on_enter(self, query):
        action_list = ActionList()
        if query.get_keyword() == self.keyword and query.get_argument():
            argument = query.get_argument()
        elif self.is_default_search:
            argument = query
        else:
            argument = None

        if argument:
            action_list.append(OpenUrlAction(self.url % argument))
        else:
            action_list.append(SetUserQueryAction('%s ' % self.keyword))

        return action_list
