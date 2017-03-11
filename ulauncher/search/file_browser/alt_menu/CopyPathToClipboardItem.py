from ulauncher.utils.icon_loader import get_themed_icon_by_name
from ulauncher.result_list.result_item.SmallResultItem import SmallResultItem
from ulauncher.result_list.item_action.ActionList import ActionList
from ulauncher.result_list.item_action.CopyToClipboardAction import CopyToClipboardAction


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
