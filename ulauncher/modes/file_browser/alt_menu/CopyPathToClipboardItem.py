from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.SmallResultItem import SmallResultItem
from ulauncher.utils.image_loader import get_themed_icon_by_name


class CopyPathToClipboardItem(SmallResultItem):
    """
    :param ~ulauncher.utils.Path.Path path:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, path):
        self.path = path

    def get_name(self):
        return 'Copy Path to Clipboard'

    # pylint: disable=super-init-not-called, arguments-differ
    def get_name_highlighted(self, *args):
        pass

    def get_icon(self):
        return get_themed_icon_by_name('edit-copy', self.get_icon_size())

    def on_enter(self, query):
        return CopyToClipboardAction(self.path.get_abs_path())
