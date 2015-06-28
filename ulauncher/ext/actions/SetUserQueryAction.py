from gi.repository import Gtk
from ulauncher.utils.run_async import run_async
from time import sleep
from .BaseAction import BaseAction


class SetUserQueryAction(BaseAction):

    def __init__(self, new_query):
        self.new_query = new_query
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        self._input = UlauncherWindow.get_instance().input

    def keep_app_open(self):
        return True

    def run(self):
        self._input.set_text(self.new_query)
        self.set_position()

    @run_async
    def set_position(self):
        # Ugly hack:
        # Defer set position, because GTK sets position after change event occurs
        sleep(0.002)
        self._input.set_position(len(self.new_query))
