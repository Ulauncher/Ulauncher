from ulauncher.api import SmallResult
from ulauncher.api.shared.action.OpenAction import OpenAction


class OpenFolderItem(SmallResult):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path, name='Open Folder'):
        self.path = path
        self._name = name

    # pylint: disable=arguments-differ
    def get_name_highlighted(self, *args):
        pass

    def get_name(self):
        return self._name

    def get_icon(self):
        return 'system-file-manager'

    def on_enter(self, query):
        return OpenAction(self.path)
