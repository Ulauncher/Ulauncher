from ulauncher.ext.ResultItem import ResultItem
from ulauncher.ext.actions.LaunchAppAction import LaunchAppAction
from ulauncher.ext.actions.ActionList import ActionList
from .AppQueryDb import AppQueryDb


class AppResultItem(ResultItem):

    def __init__(self, record):
        """
        :param dict record:
        """
        self.record = record
        self._app_queries = AppQueryDb.get_instance()

    def get_name(self):
        return self.record.get('name')

    def get_description(self, query):
        return self.record.get('description')

    def selected_by_default(self, query):
        """
        :param Query query:
        """
        return self._app_queries.find(str(query)) == self.record.get('name')

    def get_icon(self):
        return self.record.get('icon')

    def on_enter(self, query):
        self._app_queries.put(query, self.record.get('name'))
        self._app_queries.commit()
        return ActionList((LaunchAppAction(self.record.get('desktop_file')),))
