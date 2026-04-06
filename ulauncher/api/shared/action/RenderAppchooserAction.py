from gi.repository import GLib
from .BaseAction import BaseAction


class RenderAppchooserAction(BaseAction):
    """
    Renders list of result items

    :param list result_list: list of :class:`~ulauncher.api.shared.item.ResultItem.ResultItem` objects
    """

    def __init__(self, path):
        self.path = path

    def keep_app_open(self):
        return True

    def run(self):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

        window = UlauncherWindow.get_instance()
        if window.is_visible():
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(window.show_appchooser, self.path)
