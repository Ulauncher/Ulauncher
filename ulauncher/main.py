import sys
import os
import signal
import logging
import time
from locale import gettext as _
from threading import Event

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from .helpers import parse_options
from .config import get_version, CACHE_DIR, CONFIG_DIR
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.utils.Settings import Settings
from ulauncher.utils.run_async import run_async
from ulauncher.utils.setup_logging import setup_logging


DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'


def _create_dirs():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

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


class GracefulAppKiller(object):

    _exit_event = None

    def __init__(self):
        self._exit_event = Event()
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def killed(self):
        return self._exit_event.is_set()

    def _exit_gracefully(self, signum, frame):
        self._exit_event.set()


def main():
    _create_dirs()

    options = parse_options()
    setup_logging(options)
    logger = logging.getLogger('ulauncher')
    logger.info('Ulauncher version %s' % get_version())
    logger.info("GTK+ %s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()))

    # log uncaught exceptions
    def except_hook(exctype, value, tb):
        logger.error("Uncaught exception", exc_info=(exctype, value, tb))

    sys.excepthook = except_hook

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

        # workaround to make Ctrl+C quiting the app
        app_killer = GracefulAppKiller()
        gtk_thread = run_async(Gtk.main)()
        try:
            while gtk_thread.is_alive() and not app_killer.killed():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.warn('On KeyboardInterrupt')
        finally:
            Gtk.main_quit()
