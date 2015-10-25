import sys
import os
import optparse
import logging
import time
from locale import gettext as _
from gi.repository import Gtk

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from .helpers import set_up_logging
from .config import get_version, CACHE_DIR, CONFIG_DIR
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.utils.Settings import Settings
from ulauncher.utils.run_async import run_async


DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'


def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages"))
    parser.add_option(
        "--hide-window", action="store_true",
        help=_("Hide window upon application startup"))
    (options, args) = parser.parse_args()

    return options


def _create_dirs():
    # make sure ~/.config/ulauncher/apps exists
    apps_path = os.path.join(CONFIG_DIR, 'apps')
    if not os.path.exists(apps_path):
        os.makedirs(apps_path)

    # make sure ~/.cache/ulauncher exists
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


class UlauncherDbusService(dbus.service.Object):
    def __init__(self, window):
        self.window = window
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus())
        super(UlauncherDbusService, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_SERVICE)
    def show_window(self):
        self.window.show_window()


def main():
    _create_dirs()

    options = parse_options()
    set_up_logging(options)
    logger = logging.getLogger('ulauncher')
    logger.info('Ulauncher version: %s' % get_version())

    # start DBus loop
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    instance = bus.request_name(DBUS_SERVICE)

    if instance != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        logger.debug("Getting the existing instance...")
        show_window = dbus.SessionBus().get_object(DBUS_SERVICE, DBUS_PATH).get_dbus_method("show_window")
        show_window()
    else:
        logger.debug("Starting a new instance...")
        window = UlauncherWindow.get_instance()
        UlauncherDbusService(window)
        if not options.hide_window:
            window.show()

        if Settings.get_instance().get_property('show-indicator-icon'):
            AppIndicator.get_instance().show()

        @run_async
        def run_main():
            Gtk.main()

        main_thread = run_main()

        # workaround to make Ctrl+C quiting the app
        try:
            while main_thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info('On KeyboardInterrupt')
            Gtk.main_quit()
            main_thread.join()

    sys.exit(0)
