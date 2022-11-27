from gi.repository import GLib
from ulauncher.api.shared.action.BaseAction import BaseAction


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
        # pylint: disable=import-outside-toplevel
        from ulauncher.ui.UlauncherApp import UlauncherApp
        UlauncherApp().query = self.new_query
