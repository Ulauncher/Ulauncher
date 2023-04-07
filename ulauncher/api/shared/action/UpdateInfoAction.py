from ulauncher.api.shared.action.BaseAction import BaseAction
from gi.repository import Gio, GLib
import logging

logger = logging.getLogger()


class UpdateInfoAction(BaseAction):

    def __init__(self, info, keep_app_open=False):
        self._info = info
        self.keep_app_open = keep_app_open

    def run(self):
        # pylint: disable=import-outside-toplevel
        app = Gio.Application.get_default()

        if not app:
            logger.error("RenderResultListAction.run() should only be called by Ulauncher")
        elif not hasattr(app, "window") or not app.window.is_visible():
            logger.warning("RenderResultListAction called, but no Ulauncher window is open")
        else:
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(app.window.set_info, self._info)
