from __future__ import annotations

import ulauncher.interfaces
from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class CopyPath(Result):
    compact = True
    name = "Copy Path to Clipboard"
    icon = "edit-copy"

    def on_activation(self, _query: Query, _alt: bool = False) -> ulauncher.interfaces.ActionMetadata:
        return actions.copy(self.path)


class OpenFolder(Result):
    compact = True
    icon = "system-file-manager"
    path = ""

    def on_activation(self, _query: Query, _alt: bool = False) -> ulauncher.interfaces.ActionMetadata:
        return actions.open(self.path)
