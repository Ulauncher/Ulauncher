from __future__ import annotations

from os.path import basename

from ulauncher.internals.result import Result
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path


class FileResult(Result):
    compact = True
    highlightable = True
    path = ""
    actions = {
        "open": {"name": "Open file", "icon": "document-open"},
        "open_parent": {"name": "Open containing folder", "icon": "folder-open"},
        "copy_path": {"name": "Copy path", "icon": "edit-copy"},
    }

    def __init__(self, path: str) -> None:
        super().__init__(
            path=path,
            name=basename(path),
            icon=get_icon_from_path(path),
        )

    def get_highlightable_input(self, query_str: str) -> str:
        return basename(query_str)


class FolderResult(FileResult):
    actions = {
        "go_to": {"name": "Open", "icon": "folder-open"},
        "open": {"name": "Open in file manager", "icon": "system-file-manager"},
        "copy_path": {"name": "Copy path", "icon": "edit-copy"},
    }
