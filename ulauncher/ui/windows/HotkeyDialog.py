import logging
from gi.repository import Gtk, Gdk, GObject


logger = logging.getLogger()

FORBIDDEN_ACCEL_KEYS = (
    "Delete",
    "Page_Down",
    "Page_Up",
    "Home",
    "End",
    "Up",
    "Down",
    "Left",
    "Right",
    "Return",
    "BackSpace",
    "Alt_L",
    "Alt_R",
    "Shift_L",
    "Shift_R",
    "Control_L",
    "Control_R",
    "space",
    "Escape",
    "Tab",
    "Insert",
)


class HotkeyDialog(Gtk.ApplicationWindow):
    _accel_name = None
    _display_name = None
    __gsignals__ = {
        # parameters: <hotkey-value (str)>, <hotkey-display-value (str)>
        "hotkey-set": (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING, GObject.TYPE_STRING))
    }

    def __init__(self):
        super().__init__(
            modal=True,
            resizable=False,
            title="New Hotkey",
            type_hint="dialog",
        )

        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=5,
            margin_bottom=5,
            margin_start=10,
            margin_end=10,
        )

        label = Gtk.Label()
        label.set_markup("<i>Set a new hotkey and press Enter</i>")
        vbox.pack_start(label, True, True, 5)

        self._hotkey_input = Gtk.Entry(editable=False)
        vbox.pack_start(self._hotkey_input, True, True, 5)
        self.add(vbox)
        self.show_all()
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key_press)

    def on_destroy(self, *args):
        self.hide()
        return True

    def on_key_press(self, _, event):
        # remove GDK_MOD2_MASK, because it seems unnecessary
        mask = event.state
        if mask & Gdk.ModifierType.MOD2_MASK:
            mask ^= Gdk.ModifierType.MOD2_MASK
        if mask & Gdk.ModifierType.MOD4_MASK:
            mask ^= Gdk.ModifierType.MOD4_MASK

        accel_name = Gtk.accelerator_name(event.keyval, mask)
        display_name = Gtk.accelerator_get_label(event.keyval, mask)

        if accel_name == "Return":
            # emit hotkey-set signal
            self.emit("hotkey-set", self._accel_name, self._display_name)
            self.hide()

        if accel_name == "Escape":
            self.hide()
            return

        # do nothing for invalid hotkeys
        if not self.is_valid_hotkey(display_name, accel_name):
            logger.debug("Invalid hotkey '%s', ('%s') is not allowed", display_name, accel_name)
            return

        self._accel_name = accel_name
        self._display_name = display_name
        self._hotkey_input.set_text(display_name)

    def is_valid_hotkey(self, label, accel_name):
        """
        :param str label: String like 'Ctrl+`'
        :param str accel_name: String like '<Primary>space'

        accel_name should not be in FORBIDDEN_ACCEL_KEYS
        and label should consist of more than one symbol

        NOTE: it's very likely these verifications are not enough,
        but I could not find more information about this topic
        """
        return (accel_name not in FORBIDDEN_ACCEL_KEYS) and len(label) > 1 and not accel_name.startswith("KP_")
