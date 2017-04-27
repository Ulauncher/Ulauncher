import os

from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem
from ulauncher.util.Path import Path
from ulauncher.util.image_loader import get_file_icon
from .FileQueries import FileQueries

from .alt_menu.CopyPathToClipboardItem import CopyPathToClipboardItem
from .alt_menu.OpenFolderItem import OpenFolderItem


class FileBrowserResultItem(SmallResultItem):
    """
    :param ~ulauncher.util.Path.Path path:
    """

    def __init__(self, path):
        self.path = path
        self._file_queries = FileQueries.get_instance()

    def get_name(self):
        """
        :return: name to show in the list
        """
        return self.path.get_basename()

    def get_name_highlighted(self, query, color):
        query = os.path.basename(query)
        return super(FileBrowserResultItem, self).get_name_highlighted(query, color)

    def get_icon(self):
        return get_file_icon(self.path, self.ICON_SIZE)

    def on_enter(self, query):
        self._file_queries.put(self.path.get_abs_path())
        if self.path.is_dir():
            return SetUserQueryAction(os.path.join(self.path.get_user_path(), ''))
        else:
            return OpenAction(self.path.get_abs_path())

    def on_alt_enter(self, query):
        menu_items = self._get_dir_alt_menu() if self.path.is_dir() else self._get_file_alt_menu()
        return RenderResultListAction(menu_items)

    def _get_dir_alt_menu(self):
        """
        :rtype: list of ResultItems
        """
        open_folder = OpenFolderItem(self.path)
        open_folder.set_name("Open Folder '%s'" % self.path.get_basename())
        return [open_folder, CopyPathToClipboardItem(self.path)]

    def _get_file_alt_menu(self):
        """
        :rtype: list of ResultItems
        """
        open_folder = OpenFolderItem(Path(self.path.get_dirname()))
        open_folder.set_name('Open Containing Folder')
        return [open_folder, CopyPathToClipboardItem(self.path)]
