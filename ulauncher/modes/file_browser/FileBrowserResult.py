from os.path import basename, dirname, isdir, join

from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.query import Query
from ulauncher.modes.file_browser.CopyPathToClipboardResult import CopyPathToClipboardResult
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path
from ulauncher.modes.file_browser.OpenFolderResult import OpenFolderResult
from ulauncher.utils.fold_user_path import fold_user_path


class FileBrowserResult(Result):
    compact = True
    highlightable = True
    path = ""

    """
    :param ~str path:
    """

    def __init__(self, path):
        super().__init__(
            path=path,
            name=basename(path),
            icon=get_icon_from_path(path),
        )

    def get_highlightable_input(self, query: Query):
        return basename(query)

    def on_activation(self, _, alt=bool):
        if not alt:
            if isdir(self.path):
                return join(fold_user_path(self.path), "")

            return OpenAction(self.path)

        if isdir(self.path):
            open_folder = OpenFolderResult(name=f'Open Folder "{basename(self.path)}"', path=self.path)
        else:
            open_folder = OpenFolderResult(name="Open Containing Folder", path=dirname(self.path))

        return [open_folder, CopyPathToClipboardResult(path=self.path)]
