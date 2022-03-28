import logging
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk, GObject

from ulauncher.ui.windows.Builder import GladeObjectFactory


logger = logging.getLogger('ulauncher')

FORBIDDEN_ACCEL_KEYS = ('Delete', 'Page_Down', 'Page_Up', 'Home', 'End', 'Up', 'Down', 'Left', 'Right', 'Return',
                        'BackSpace', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'space',
                        'Escape', 'Tab', 'Insert')


class HotkeyDialog(Gtk.Dialog):
    __gtype_name__ = "HotkeyDialog"

    __gsignals__ = {
        # parameters: <hotkey-value (str)>, <hotkey-display-value (str)>
        'hotkey-set': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING, GObject.TYPE_STRING))
    }

    _accel_name = None
    _display_name = None

    # Python's GTK API seems to requires non-standard workarounds like this.
    # Use finish_initializing instead of __init__.
    def __new__(cls):
        return GladeObjectFactory(cls.__name__, "hotkey_dialog")

    def finish_initializing(self, ui):
        # pylint: disable=attribute-defined-outside-init
        self.ui = ui
        self.ui['hotkey_dialog_action_area'].destroy()

    def on_delete_event(self, *args):
        # don't delete. Hide instead
        self.hide()
        return True

    def on_hotkey_input_key_press_event(self, _, event):
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

        self.ui['hotkey_input'].set_text(display_name)

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
