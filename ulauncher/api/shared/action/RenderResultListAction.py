from gi.repository import GLib
from ulauncher.api.shared.action.BaseAction import BaseAction


class RenderResultListAction(BaseAction):
    """
    Renders list of result items

    :param list result_list: list of :class:`~ulauncher.api.result.Result` objects
    """

    keep_app_open = True

    def __init__(self, result_list):
        self.result_list = result_list

    def run(self):
        # pylint: disable=import-outside-toplevel
        from ulauncher.ui.UlauncherApp import UlauncherApp

        window = UlauncherApp().window
        if window.is_visible():
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(window.show_results, self.result_list)
