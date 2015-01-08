# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import optparse
import os

from locale import gettext as _

from gi.repository import Gtk # pylint: disable=E0611

from ulauncher import UlauncherWindow

from ulauncher_lib import set_up_logging, get_version
from ulauncher_lib import IconTray


def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs ulauncher_lib also)"))
    (options, args) = parser.parse_args()

    set_up_logging(options)


def main():
    'constructor for your class instances'
    parse_options()

    # Run the application.
    window = UlauncherWindow.UlauncherWindow()
    window.show()

    tray_indicator = IconTray.IconoTray("ulauncher")
    tray_indicator.set_icon(os.getcwd() + '/data/media/default_app_icon.png')
    tray_indicator.add_menu_item(window.on_mnu_preferences_activate, "Preferences")
    tray_indicator.add_menu_item(window.on_mnu_about_activate, "About")
    tray_indicator.add_seperator()
    tray_indicator.add_menu_item(Gtk.main_quit, "Exit")

    Gtk.main()
