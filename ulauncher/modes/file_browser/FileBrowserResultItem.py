import os
import mimetypes
import gi
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib

from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem
from ulauncher.utils.Path import Path
from ulauncher.utils.icon import load_icon

from ulauncher.modes.file_browser.FileQueries import FileQueries
from ulauncher.modes.file_browser.alt_menu.CopyPathToClipboardItem import CopyPathToClipboardItem
from ulauncher.modes.file_browser.alt_menu.OpenFolderItem import OpenFolderItem

SPECIAL_DIRS = {
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD): 'folder-download',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS): 'folder-documents',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC): 'folder-music',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES): 'folder-pictures',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE): 'folder-publicshare',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES): 'folder-templates',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS): 'folder-videos',
    GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP): 'user-desktop',
    os.path.expanduser('~'): 'folder-home'
}


class FileBrowserResultItem(SmallResultItem):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
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
        return super().get_name_highlighted(query, color)

    def get_file_icon(self):
        if self.path.is_dir():
            return SPECIAL_DIRS.get(str(self.path)) or "folder"

        mime = mimetypes.guess_type(self.path.get_basename())[0]
        if mime:
            return mime.replace("/", "-")

        if self.path.is_exe():
            return "application-x-executable"

        return "unknown"

    def get_icon(self):
        return load_icon(self.get_file_icon(), self.get_icon_size())

    def on_enter(self, query):
        self._file_queries.save_query(self.path.get_abs_path())
        if self.path.is_dir():
            return SetUserQueryAction(os.path.join(self.path.get_user_path(), ''))

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
