from ulauncher.api.result import Result
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


class CopyPathToClipboardItem(Result):
    compact = True

    # pylint: disable=super-init-not-called
    def __init__(self, path: str):
        self.path = path
        self.name = "Copy Path to Clipboard"
        self.icon = "edit-copy"

    def on_activation(self, *_):
        return CopyToClipboardAction(self.path)
