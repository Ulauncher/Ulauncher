from ulauncher.api import SmallResult
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


class CopyPathToClipboardItem(SmallResult):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path):
        self.path = path
        self.name = 'Copy Path to Clipboard'
        self.icon = 'edit-copy'

    def on_enter(self, query):
        return CopyToClipboardAction(self.path)
