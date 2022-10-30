from time import sleep
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
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        input = UlauncherWindow.get_instance().input
        input.set_text(self.new_query)

        # Ugly hack:
        # Defer set position, because GTK sets position after change event occurs
        sleep(0.002)
        input.set_position(-1)
