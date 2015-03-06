# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-


# This is your preferences dialog.
#
# Define your preferences in
# data/glib-2.0/schemas/net.launchpad.ulauncher.gschema.xml
# See http://developer.gnome.org/gio/stable/GSettings.html for more info.

from gi.repository import Gio  # pylint: disable=E0611

from locale import gettext as _

import logging
logger = logging.getLogger('ulauncher')

from ulauncher_lib.PreferencesDialog import PreferencesDialog


class PreferencesUlauncherDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesUlauncherDialog"

    def finish_initializing(self, builder):  # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesUlauncherDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        settings = Gio.Settings("net.launchpad.ulauncher")
        widget = self.builder.get_object('example_entry')
        settings.bind("example", widget, "text", Gio.SettingsBindFlags.DEFAULT)

        # Code for other initialization actions should be added here.
