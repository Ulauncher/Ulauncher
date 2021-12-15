import os
import mimetypes
from pathlib import Path
import gi
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib

from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.api import SmallResult
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
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


class FileBrowserResult(SmallResult):
    """
    :param ~str path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path):
        self.path = path
        self._file_queries = FileQueries.get_instance()

    def get_name(self):
        """
        :return: name to show in the list
        """
        return Path(self.path).name

    def get_name_highlighted(self, query, color):
        query = os.path.basename(query)
        return super().get_name_highlighted(query, color)

    def get_icon(self):
        if Path(self.path).is_dir():
            return SPECIAL_DIRS.get(self.path) or "folder"

        mime = mimetypes.guess_type(Path(self.path).name)[0]
        if mime:
            return mime.replace("/", "-")

        if os.access(self.path, os.X_OK):
            return "application-x-executable"

        return "unknown"

    def on_enter(self, query):
        self._file_queries.save_query(self.path)
        if Path(self.path).is_dir():
            return SetUserQueryAction(os.path.join(fold_user_path(self.path), ''))

        return OpenAction(self.path)

    def on_alt_enter(self, query):
        if Path(self.path).is_dir():
            open_folder = OpenFolderItem(self.path, f'Open Folder "{Path(self.path).name}"')
        else:
            open_folder = OpenFolderItem(str(Path(self.path).parent), 'Open Containing Folder')
        return [open_folder, CopyPathToClipboardItem(self.path)]
