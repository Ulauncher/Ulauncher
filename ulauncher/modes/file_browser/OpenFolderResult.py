from ulauncher.api.result import Result
from ulauncher.api.shared.action.OpenAction import OpenAction


class OpenFolderResult(Result):
    compact = True
    icon = "system-file-manager"
    path = ""

    def on_activation(self, *_):
        return OpenAction(self.path)
