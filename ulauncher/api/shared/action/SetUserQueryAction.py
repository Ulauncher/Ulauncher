import logging
from gi.repository import Gio, GLib
from ulauncher.api.shared.action.BaseAction import BaseAction

logger = logging.getLogger()


class SetUserQueryAction(BaseAction):
    """
    Changes query string to a new one
    """

    keep_app_open = True

    def __init__(self, new_query: str):
        self.new_query = new_query

    def run(self):
        GLib.idle_add(self._update_query)

    def _update_query(self):
        app = Gio.Application.get_default()

        if app and hasattr(app, "query"):
            app.query = self.new_query
        else:
            logger.error("SetUserQueryAction.run() should only be called by Ulauncher")
