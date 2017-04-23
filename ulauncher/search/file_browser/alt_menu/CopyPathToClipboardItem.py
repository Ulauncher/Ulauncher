from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem
from ulauncher.util.image_loader import get_themed_icon_by_name


class CopyPathToClipboardItem(SmallResultItem):
    """
    :param ~ulauncher.util.Path.Path path:
    """

    def __init__(self, path):
        self.path = path

    def get_name(self):
        return 'Copy Path to Clipboard'

    def get_name_highlighted(serlf, *args):
        pass

    def get_icon(self):
        return get_themed_icon_by_name('edit-copy', self.ICON_SIZE)

    def on_enter(self, query):
        return CopyToClipboardAction(self.path.get_abs_path())
