from __future__ import annotations

from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class CopyPathToClipboardResult(Result):
    compact = True
    name = "Copy Path to Clipboard"
    icon = "edit-copy"

    def on_activation(self, _query: Query, _alt: bool = False) -> dict[str, str]:
        return CopyToClipboardAction(self.path)
