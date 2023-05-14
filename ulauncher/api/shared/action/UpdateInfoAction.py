import logging
from gi.repository import Gio, GLib
from ulauncher.api.shared.action.BaseAction import BaseAction

logger = logging.getLogger()


class UpdateInfoAction(BaseAction):
    def __init__(self, info, base_url="file:///", keep_app_open=False):
        self._info = info
        self.base_url = base_url
        self.keep_app_open = keep_app_open

    def run(self):
        # pylint: disable=import-outside-toplevel
        app = Gio.Application.get_default()

        if not app:
            logger.error("UpdateInfoAction.run() should only be called by Ulauncher")
        elif not hasattr(app, "window") or not app.window.is_visible():
            logger.warning("UpdateInfoAction called, but no Ulauncher window is open")
        else:
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(app.window.set_info, self._info, self.base_url)
