import logging
from types import SimpleNamespace

from gi.repository import Gdk, Gtk

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
        self.connect("key-press-event", self.on_key_press)

    def handle_response(self, _widget, response_id: int):
        if response_id == RESPONSES.OK:
            self.save_and_close()
        if response_id == RESPONSES.CLOSE:
            self.close()

    def set_hotkey(self, key_name=""):
        label = Gtk.accelerator_get_label(*Gtk.accelerator_parse(key_name))
        self._hotkey = key_name
        self._hotkey_input.set_text(label)
        self._hotkey_input.set_position(-1)
        self.set_response_sensitive(RESPONSES.OK, bool(key_name))

    def close(self):
        self._hotkey = ""
        self.hide()

    def save_and_close(self):
        self.hide()

    def on_key_press(self, _, event: Gdk.EventKey):
        key_name = Gtk.accelerator_name(event.keyval, event.state)
        label = Gtk.accelerator_get_label(event.keyval, event.state)
        breadcrumb = label.split("+")

        # treat Enter w/o modifiers as "submit"
        if self._hotkey and key_name == "Return":
            self.save_and_close()

        if self._hotkey and key_name == "BackSpace":
            self.set_hotkey()

        # Must have at least one modifier (meaning two parts) and the last part must not be one
        if len(breadcrumb) > 1 and breadcrumb[-1] not in MODIFIERS:
            self.set_hotkey(key_name)

    def run(self):
        super().run()
        return self._hotkey
