from ulauncher.utils.icon_loader import get_themed_icon_by_name
from ulauncher.ext.SmallResultItem import SmallResultItem
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.CopyToClipboardAction import CopyToClipboardAction


class CopyPathToClipboardItem(SmallResultItem):

    def __init__(self, path):
        """
        :param Path path:
        """
        self.path = path

    def get_name(self):
        return 'Copy Path to Clipboard'

    def get_name_highlighted(serlf, *args):
        pass

    def get_icon(self):
        return get_themed_icon_by_name('edit-copy', self.ICON_SIZE)

    def on_enter(self, query):
        return ActionList([CopyToClipboardAction(self.path.get_abs_path())])
