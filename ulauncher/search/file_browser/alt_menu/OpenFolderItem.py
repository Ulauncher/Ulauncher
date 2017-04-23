from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem
from ulauncher.util.image_loader import get_themed_icon_by_name


class OpenFolderItem(SmallResultItem):
    """
    :param ~ulauncher.util.Path.Path path:
    """

    def __init__(self, path):
        self.path = path
        self._name = 'Open Folder'

    def set_name(self, name):
        self._name = name

    def get_name_highlighted(self, *args):
        pass

    def get_name(self):
        return self._name

    def get_icon(self):
        return get_themed_icon_by_name('system-file-manager', self.ICON_SIZE)

    def on_enter(self, query):
        return OpenAction(self.path.get_abs_path())
