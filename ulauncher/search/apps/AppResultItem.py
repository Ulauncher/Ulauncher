from ulauncher.ext.ResultItem import ResultItem
from ulauncher.ext.actions.LaunchAppAction import LaunchAppAction
from ulauncher.ext.actions.ActionList import ActionList


class AppResultItem(ResultItem):

    def __init__(self, record):
        """
        :param dict record:
        """
        self.record = record

    def get_name(self):
        return self.record.get('name')

    def get_description(self, query):
        return self.record.get('description')

    def get_icon(self):
        return self.record.get('icon')

    def on_enter(self, query):
        return ActionList((LaunchAppAction(self.record.get('desktop_file')),))
