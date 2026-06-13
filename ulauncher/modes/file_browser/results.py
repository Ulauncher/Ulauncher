from __future__ import annotations

from os.path import basename, isdir
from typing import Dict, Literal

from ulauncher.internals.result import Result
from ulauncher.modes.file_browser.get_icon_from_path import get_icon_from_path

_Actions = Dict[str, Dict[Literal["name", "icon"], str]]

_FILE_ACTIONS: _Actions = {
    "open": {"name": "Open file", "icon": "document-open"},
    "open_with": {"name": "Open with...", "icon": "system-run"},
    "open_parent": {"name": "Open containing folder", "icon": "folder-open"},
    "copy_path": {"name": "Copy path", "icon": "edit-copy"},
}
_FOLDER_ACTIONS: _Actions = {
    "go_to": {"name": "Open", "icon": "folder-open"},
    "open": {"name": "Open in file manager", "icon": "system-file-manager"},
    "open_with": {"name": "Open with...", "icon": "system-run"},
    "copy_path": {"name": "Copy path", "icon": "edit-copy"},
}


class FileResult(Result):
    compact = True
    highlightable = True
    path = ""

    def __init__(self, path: str) -> None:
        is_dir = isdir(path)
        super().__init__(
            path=path,
            name=basename(path),
            icon=get_icon_from_path(path, is_dir),
            actions=_FOLDER_ACTIONS if is_dir else _FILE_ACTIONS,
        )

    def get_highlightable_input(self, query_str: str) -> str:
        return basename(query_str)
