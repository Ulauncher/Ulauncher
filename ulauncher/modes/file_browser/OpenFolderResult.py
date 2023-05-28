from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction


class OpenFolderResult(Result):
    compact = True
    icon = "system-file-manager"

    # pylint: disable=super-init-not-called
    def __init__(self, path: str, name="Open Folder"):
        self.path = path
        self.name = name

    def on_activation(self, *_):
        return OpenAction(self.path)
