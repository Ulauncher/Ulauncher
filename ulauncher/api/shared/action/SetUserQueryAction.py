from time import sleep
import gi
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib

from ulauncher.api.shared.action.BaseAction import BaseAction


class SetUserQueryAction(BaseAction):
    """
    Changes query string to a new one

    :param str new_query:
    """

    def __init__(self, new_query):
        self.new_query = new_query

    def keep_app_open(self):
        return True

    def run(self):
        GLib.idle_add(self._update_query)

    def _update_query(self):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

        input = UlauncherWindow.get_instance().get_input()
        input.set_text(self.new_query)

        # Ugly hack:
        # Defer set position, because GTK sets position after change event occurs
        sleep(0.002)
        input.set_position(len(self.new_query))
