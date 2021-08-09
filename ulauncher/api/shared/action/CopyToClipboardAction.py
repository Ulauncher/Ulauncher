import gi
# pylint: disable=wrong-import-position
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

from ulauncher.api.shared.action.BaseAction import BaseAction


class CopyToClipboardAction(BaseAction):
    """
    Copy text to the clipboard

    :param str text: text to copy
    """

    def __init__(self, text):
        self.text = text

    def keep_app_open(self):
        return False

    def run(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.text, -1)
        clipboard.store()
