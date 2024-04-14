from __future__ import annotations

from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.query import Query


class OpenFolderResult(Result):
    compact = True
    icon = "system-file-manager"
    path = ""

    def on_activation(self, _query: Query, _alt: bool = False) -> dict[str, str]:
        return OpenAction(self.path)
