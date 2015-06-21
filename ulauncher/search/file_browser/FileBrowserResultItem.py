import os
from ulauncher.utils.icon_loader import get_file_icon
from ulauncher.ext.SmallResultItem import SmallResultItem
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.OpenAction import OpenAction
from .FileQueries import FileQueries


class FileBrowserResultItem(SmallResultItem):

    def __init__(self, path):
        """
        :param Path path:
        """
        self.path = path
        self._file_queries = FileQueries.get_instance()

    def get_name(self):
        """
        Return name to show in the list
        """
        return self.path.get_basename()

    def get_icon(self):
        return get_file_icon(str(self.path), self.ICON_SIZE)

    def on_enter(self, query):
        self._file_queries.put(str(self.path))
        if self.path.is_dir():
            return ActionList([SetUserQueryAction(os.path.join(self.path.get_user_path(), ''))])
        else:
            return ActionList([OpenAction(str(self.path))])
