import os
from pathlib import Path
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.api import SmallResult
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.modes.file_browser.FileQueries import FileQueries
from ulauncher.modes.file_browser.alt_menu.CopyPathToClipboardItem import CopyPathToClipboardItem
from ulauncher.modes.file_browser.alt_menu.OpenFolderItem import OpenFolderItem
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path


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
        return get_icon_from_path(self.path)

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
