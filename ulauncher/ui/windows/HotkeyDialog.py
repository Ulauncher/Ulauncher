import logging
from types import SimpleNamespace

from gi.repository import Gdk, Gtk

from ulauncher.utils.hotkey_controller import HotkeyController

logger = logging.getLogger()
footer_notice = "Be aware that keyboard shortcuts may be reserved by, or conflict with your system."

RESPONSES = SimpleNamespace(OK=-5, CLOSE=-7)

MODIFIERS = (
    "Alt_L",
    "Alt_R",
    "Shift_L",
    "Shift_R",
    "Control_L",
    "Control_R",
    "Super_L",
)


class HotkeyDialog(Gtk.MessageDialog):
    _hotkey = ""

    def __init__(self):
        super().__init__(title="Set new hotkey", flags=Gtk.DialogFlags.MODAL)
        self.add_buttons("Close", Gtk.ResponseType.CLOSE, "Save", Gtk.ResponseType.OK)
        self.set_response_sensitive(RESPONSES.OK, False)

        vbox = Gtk.Box(orientation="vertical", margin_start=10, margin_end=10)
        self._hotkey_input = Gtk.Entry(editable=False)
        vbox.pack_start(self._hotkey_input, True, True, 5)
        vbox.pack_start(Gtk.Label(use_markup=True, label=f"<i><small>{footer_notice}</small></i>"), True, True, 5)
        self.get_content_area().add(vbox)

        self.show_all()
        self.connect("response", self.handle_response)
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key_press)

    def handle_response(self, _widget, response_id: int):
        if response_id == RESPONSES.OK:
            HotkeyController.set(self._hotkey)
            self.hide()
        if response_id == RESPONSES.CLOSE:
            self.hide()

    def on_destroy(self, *_args):
        self.hide()
        return True

    def on_key_press(self, _, event: Gdk.EventKey):
        key_name = Gtk.accelerator_name(event.keyval, event.state)
        display_name = Gtk.accelerator_get_label(event.keyval, event.state)
        breadcrumb = display_name.split("+")

        # treat Enter w/o modifiers as "submit"
        if self._hotkey and key_name == "Return":
            HotkeyController.set(self._hotkey)
            self.hide()

        # Must have at least one modifier (meaning two parts) and the last part must not be one
        if len(breadcrumb) > 1 and breadcrumb[-1] not in MODIFIERS:
            self._hotkey = key_name
            self._hotkey_input.set_text(display_name)
            self.set_response_sensitive(RESPONSES.OK, True)
