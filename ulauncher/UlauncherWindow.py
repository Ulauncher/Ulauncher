# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

from locale import gettext as _

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('ulauncher')

from ulauncher_lib import Window
from ulauncher.AboutUlauncherDialog import AboutUlauncherDialog
from ulauncher.PreferencesUlauncherDialog import PreferencesUlauncherDialog

# See ulauncher_lib.Window.py for more details about how this class works
class UlauncherWindow(Window):
    __gtype_name__ = "UlauncherWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UlauncherWindow, self).finish_initializing(builder)
        w = Gtk.Window()

        self.AboutDialog = AboutUlauncherDialog
        self.PreferencesDialog = PreferencesUlauncherDialog

        # Code for other initialization actions should be added here.

