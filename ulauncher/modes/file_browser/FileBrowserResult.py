from os.path import basename, dirname, isdir, join
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.api import SmallResult
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.modes.file_browser.FileQueries import FileQueries
from ulauncher.modes.file_browser.alt_menu.CopyPathToClipboardItem import CopyPathToClipboardItem
from ulauncher.modes.file_browser.alt_menu.OpenFolderItem import OpenFolderItem
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path


class FileBrowserResult(SmallResult):
    highlightable = True

    """
    :param ~str path:
    """
    # pylint: disable=super-init-not-called
    def __init__(self, path):
        self.path = path
        self.name = basename(path)
        self.icon = get_icon_from_path(path)
        self._file_queries = FileQueries.get_instance()

    def get_name_highlighted(self, query, color):
        query = basename(query)
        return super().get_name_highlighted(query, color)

    def on_enter(self, _):
        self._file_queries.save_query(self.path)
        if isdir(self.path):
            return SetUserQueryAction(join(fold_user_path(self.path), ''))

        return OpenAction(self.path)

    def on_alt_enter(self, _):
        if isdir(self.path):
            open_folder = OpenFolderItem(self.path, f'Open Folder "{basename(self.path)}"')
        else:
            open_folder = OpenFolderItem(dirname(self.path), 'Open Containing Folder')
        return [open_folder, CopyPathToClipboardItem(self.path)]
