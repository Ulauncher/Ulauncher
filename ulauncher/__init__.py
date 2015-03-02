# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import sys
import optparse
import logging
from locale import gettext as _

import dbus
import dbus.service
from gi.repository import Gtk  # pylint: disable=E0611
from dbus.mainloop.glib import DBusGMainLoop

from ulauncher import UlauncherWindow, Indicator
from ulauncher_lib import set_up_logging, get_version
from ulauncher_lib.ulauncherconfig import get_data_file


DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'


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

        indicator = Indicator.Indicator("ulauncher")
        indicator.set_icon(get_data_file('media', 'default_app_icon.png'))
        indicator.add_menu_item(window.on_mnu_preferences_activate, "Preferences")
        indicator.add_menu_item(window.on_mnu_about_activate, "About")
        indicator.add_seperator()
        indicator.add_menu_item(Gtk.main_quit, "Exit")
        indicator.show_menu()

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
