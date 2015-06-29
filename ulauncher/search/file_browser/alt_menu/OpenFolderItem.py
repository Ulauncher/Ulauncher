from ulauncher.utils.icon_loader import get_themed_icon_by_name
from ulauncher.ext.SmallResultItem import SmallResultItem
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.OpenAction import OpenAction


class OpenFolderItem(SmallResultItem):

    def __init__(self, path):
        """
        :param Path path:
        """
        self.path = path
        self._name = 'Open Folder'

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def get_icon(self):
        return get_themed_icon_by_name('system-file-manager', self.ICON_SIZE)

    def on_enter(self, query):
        return ActionList([OpenAction(str(self.path))])
