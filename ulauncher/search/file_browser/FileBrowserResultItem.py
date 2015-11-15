import os
from ulauncher.utils.icon_loader import get_file_icon
from ulauncher.ext.SmallResultItem import SmallResultItem
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.OpenAction import OpenAction
from .FileQueries import FileQueries
from ulauncher.utils.Path import Path

from .alt_menu.CopyPathToClipboardItem import CopyPathToClipboardItem
from .alt_menu.OpenFolderItem import OpenFolderItem


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
        return get_file_icon(self.path, self.ICON_SIZE)

    def on_enter(self, query):
        self._file_queries.put(self.path.get_abs_path())
        if self.path.is_dir():
            return ActionList([SetUserQueryAction(os.path.join(self.path.get_user_path(), ''))])
        else:
            return ActionList([OpenAction(self.path.get_abs_path())])

    def on_alt_enter(self, query):
        menu_items = self._get_dir_alt_menu() if self.path.is_dir() else self._get_file_alt_menu()
        return ActionList((RenderResultListAction(menu_items),))

    def _get_dir_alt_menu(self):
        "Return list of ResultItems"
        open_folder = OpenFolderItem(self.path)
        open_folder.set_name("Open Folder '%s'" % self.path.get_basename())
        return [open_folder, CopyPathToClipboardItem(self.path)]

    def _get_file_alt_menu(self):
        "Return list of ResultItems"
        open_folder = OpenFolderItem(Path(self.path.get_dirname()))
        open_folder.set_name('Open Containing Folder')
        return [open_folder, CopyPathToClipboardItem(self.path)]
