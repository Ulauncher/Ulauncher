from __future__ import annotations

from os.path import basename, dirname, isdir, join

import ulauncher.interfaces
from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.file_browser import results
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path
from ulauncher.utils.fold_user_path import fold_user_path


class FileBrowserResult(Result):
    compact = True
    highlightable = True
    path = ""

    def __init__(self, path: str) -> None:
        super().__init__(
            path=path,
            name=basename(path),
            icon=get_icon_from_path(path),
        )

    def get_highlightable_input(self, query: Query) -> str | None:
        # only highlight when you put a filter query in after the path (e.g. ~/Downloads/txt)
        if query.argument:
            return basename(query.argument)
        return None

    def on_activation(self, _query: Query, alt: bool = False) -> ulauncher.interfaces.ActionMetadata:
        if not alt:
            if isdir(self.path):
                return join(fold_user_path(self.path), "")

            return actions.open(self.path)

        if isdir(self.path):
            open_folder = results.OpenFolder(name=f'Open Folder "{basename(self.path)}"', path=self.path)
        else:
            open_folder = results.OpenFolder(name="Open Containing Folder", path=dirname(self.path))

        return [open_folder, results.CopyPath(path=self.path)]
