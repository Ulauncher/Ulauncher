# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import sys
import dbus
import dbus.service
import optparse
import os

import logging
from locale import gettext as _
from gi.repository import Gtk  # pylint: disable=E0611
from ulauncher import UlauncherWindow
from ulauncher_lib import set_up_logging, get_version
from dbus.mainloop.glib import DBusGMainLoop

from gi.repository import Gtk # pylint: disable=E0611

DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'

from ulauncher_lib import set_up_logging, get_version
from ulauncher_lib import IconTray

def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs ulauncher_lib also)"))
    (options, args) = parser.parse_args()

    return options



def main():
    options = parse_options()
    set_up_logging(options)
    logger = logging.getLogger('ulauncher')

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
    # start DBus loop
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    instance = bus.request_name(DBUS_SERVICE)

    if instance != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        logger.debug("Getting the existing instance...")
        logger.debug("Showing a main window...")
        show_window = dbus.SessionBus().get_object(DBUS_SERVICE, DBUS_PATH).get_dbus_method("show_window")
        show_window()
    else:
        logger.debug("Starting a new instance...")
        window = UlauncherWindow.UlauncherWindow()
        UlauncherDbusService(window)
        window.show()
        Gtk.main()

    sys.exit(0)


class UlauncherDbusService(dbus.service.Object):
    def __init__(self, window):
        self.window = window
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus())
        super(UlauncherDbusService, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_SERVICE)
    def show_window(self):
        self.window.show_window()
