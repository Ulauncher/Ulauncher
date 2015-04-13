# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
import logging
from gi.repository import Gio, Gtk, Gdk, Keybinder
from locale import gettext as _
from ulauncher_lib.PreferencesDialog import PreferencesDialog
from ulauncher.service_locator import getSettings, getIndicator, getUlauncherWindow


logger = logging.getLogger(__name__)

FORBIDDEN_ACCEL_KEYS = ('Delete', 'Page_Down', 'Page_Up', 'Home', 'End', 'Up', 'Down', 'Left', 'Right', 'Return',
                        'BackSpace', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'space',
                        'Escape', 'Tab', 'Insert')


class PreferencesUlauncherDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesUlauncherDialog"

    def finish_initializing(self, builder):
        """Set up the preferences dialog"""
        super(PreferencesUlauncherDialog, self).finish_initializing(builder)

        # unnecessary action area can be removed only manually, like this
        self.builder.get_object('dialog_action_area').destroy()

        self.settings = getSettings()

        # set user preferences
        indicator_switch = self.builder.get_object('show_indicator_icon')
        indicator_switch.set_active(self.settings.get_property('show-indicator-icon'))

        app_hotkey = self.builder.get_object('hotkey_show_app')
        self.app_hotkey_current_accel_name = self.settings.get_property('hotkey-show-app')
        try:
            (key, mode) = Gtk.accelerator_parse(self.app_hotkey_current_accel_name)
        except Exception:
            logger.warning('Unable to parse accelerator "%s". Use Ctrl+Space' % self.app_hotkey_current_accel_name)
            (key, mode) = Gtk.accelerator_parse("<Primary>space")
        self.app_hotkey_current_label = Gtk.accelerator_get_label(key, mode)
        app_hotkey.set_text(self.app_hotkey_current_label)

    def on_show_indicator_icon_notify(self, widget, event):
        if event.name == 'active':
            show_indicator = widget.get_active()
            self.settings.set_property('show-indicator-icon', show_indicator)
            indicator = getIndicator()
            indicator.show() if show_indicator else indicator.hide()
            self.settings.save_to_file()

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

    def on_hotkey_show_app_key_press_event(self, widget, event):
        # remove GDK_MOD2_MASK, because it seems unnecessary
        mask = event.state
        if mask & Gdk.ModifierType.MOD2_MASK:
            mask ^= Gdk.ModifierType.MOD2_MASK

        label = Gtk.accelerator_get_label(event.keyval, mask)
        accel_name = Gtk.accelerator_name(event.keyval, mask)

        # do nothing for invalid hotkeys
        if not self.is_valid_hotkey(label, accel_name):
            logger.debug("Invalid hotkey '%s', ('%s') is not allowed" % (label, accel_name))
            return

        # Bind a new key
        getUlauncherWindow().bind_show_app_hotkey(accel_name)

        widget.set_text(label)

        self.settings.set_property('hotkey-show-app', accel_name)
        self.settings.save_to_file()
