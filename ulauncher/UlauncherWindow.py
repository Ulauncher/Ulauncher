# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

from gi.repository import Gtk  # pylint: disable=E0611
import logging
logger = logging.getLogger('ulauncher')

from ulauncher_lib import Window
from ulauncher.AboutUlauncherDialog import AboutUlauncherDialog
from ulauncher.PreferencesUlauncherDialog import PreferencesUlauncherDialog


# See ulauncher_lib.Window.py for more details about how this class works
class UlauncherWindow(Window):
    __gtype_name__ = "UlauncherWindow"
    
    def finish_initializing(self, builder):  # pylint: disable=E1002
        """Set up the main window"""
        super(UlauncherWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUlauncherDialog
        self.PreferencesDialog = PreferencesUlauncherDialog

        provider = Gtk.CssProvider()
        provider.load_from_path('data/ui/Ulauncher.css')
        self.apply_css(self, provider)

        self.screen = self.get_screen()
        self.visual = self.screen.get_rgba_visual()
        if self.visual is not None and self.screen.is_composited():
            self.set_visual(self.visual)

        self.bindkeys()

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def cb_hotkeys(self, key):
        if self.is_visible():
            self.hide()
        else:
            self.show()

    def bindkeys(self):
        try:
            from gi.repository import Keybinder
            print "Trying to bind hotkeys."
            Keybinder.init()
            Keybinder.bind("<Ctrl>space", self.cb_hotkeys)
        except ImportError:
            print "Unable to import Keybinder, hotkeys not available."
