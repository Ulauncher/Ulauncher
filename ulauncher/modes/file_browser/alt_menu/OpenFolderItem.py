from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem


class OpenFolderItem(SmallResultItem):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path):
        self.path = path
        self._name = 'Open Folder'

    def set_name(self, name):
        self._name = name

    # pylint: disable=arguments-differ
    def get_name_highlighted(self, *args):
        pass

    def get_name(self):
        return self._name

    def get_icon(self):
        return 'system-file-manager'

    def on_enter(self, query):
        return OpenAction(self.path.get_abs_path())
