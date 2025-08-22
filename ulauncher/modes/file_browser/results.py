from __future__ import annotations

from os.path import basename

from ulauncher.internals.result import Result
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path


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

    def get_highlightable_input(self, query_str: str) -> str:
        return basename(query_str)


class CopyPath(Result):
    compact = True
    name = "Copy Path to Clipboard"
    icon = "edit-copy"
    path = ""


class OpenFolder(Result):
    compact = True
    icon = "system-file-manager"
    path = ""
