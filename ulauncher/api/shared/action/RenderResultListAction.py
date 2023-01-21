import logging
from gi.repository import Gio, GLib
from ulauncher.api.shared.action.BaseAction import BaseAction

logger = logging.getLogger()


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
        app = Gio.Application.get_default()

        if not app:
            logger.error("RenderResultListAction.run() should only be called by Ulauncher")
        elif not hasattr(app, "window") or not app.window.is_visible():
            logger.warning("RenderResultListAction called, but no Ulauncher window is open")
        else:
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(app.window.show_results, self.result_list)
