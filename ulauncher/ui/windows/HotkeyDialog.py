import logging
from gi.repository import Gtk, Gdk, GObject
from ulauncher.config import PATHS


logger = logging.getLogger()

FORBIDDEN_ACCEL_KEYS = ('Delete', 'Page_Down', 'Page_Up', 'Home', 'End', 'Up', 'Down', 'Left', 'Right', 'Return',
                        'BackSpace', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'space',
                        'Escape', 'Tab', 'Insert')


@Gtk.Template(filename=f"{PATHS.ASSETS}/ui/hotkey_dialog.ui")
class HotkeyDialog(Gtk.Window):
    __gtype_name__ = "HotkeyDialog"
    _accel_name = None
    _display_name = None
    __gsignals__ = {
        # parameters: <hotkey-value (str)>, <hotkey-display-value (str)>
        'hotkey-set': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING, GObject.TYPE_STRING))
    }
    _hotkey_input: Gtk.Entry  # Have to be declared on a separate line for some reason
    _hotkey_input = Gtk.Template.Child("hotkey_input")

    @Gtk.Template.Callback()
    def on_destroy(self, *args):
        self.hide()
        return True

    @Gtk.Template.Callback()
    def on_key_press(self, _, event):
        # remove GDK_MOD2_MASK, because it seems unnecessary
        mask = event.state
        if mask & Gdk.ModifierType.MOD2_MASK:
            mask ^= Gdk.ModifierType.MOD2_MASK
        if mask & Gdk.ModifierType.MOD4_MASK:
            mask ^= Gdk.ModifierType.MOD4_MASK

        accel_name = Gtk.accelerator_name(event.keyval, mask)
        display_name = Gtk.accelerator_get_label(event.keyval, mask)

        if accel_name == 'Return':
            # emit hotkey-set signal
            self.emit('hotkey-set', self._accel_name, self._display_name)
            self.hide()

        if accel_name == 'Escape':
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
        return (accel_name not in FORBIDDEN_ACCEL_KEYS) and len(label) > 1 and not accel_name.startswith('KP_')
