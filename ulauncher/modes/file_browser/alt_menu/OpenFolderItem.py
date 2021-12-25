from ulauncher.api import SmallResult
from ulauncher.api.shared.action.OpenAction import OpenAction


class OpenFolderItem(SmallResult):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path, name='Open Folder'):
        self.path = path
        self.name = name
        self.icon = 'system-file-manager'
        self.highlightable = False

    def on_enter(self, query):
        return OpenAction(self.path)
