from gi.repository import Gtk, Gdk
from ulauncher.api.shared.action.BaseAction import BaseAction


class CopyToClipboardAction(BaseAction):
    """
    Copy text to the clipboard
    """

    def __init__(self, text: str):
        self.text = text

    def run(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.text, -1)
        clipboard.store()
