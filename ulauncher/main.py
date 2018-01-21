from __future__ import print_function
import sys
import os
import signal
import logging
import time
from threading import Event

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from .config import (get_version, get_options, is_wayland, is_wayland_compatibility_on,
                     gdk_backend, CACHE_DIR, CONFIG_DIR)
from ulauncher.util.decorator.run_async import run_async
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.util.Settings import Settings
from ulauncher.util.setup_logging import setup_logging


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
    def toggle_window(self):
        self.window.toggle_window()


class SignalHandler(object):

    _exit_event = None
    _app_window = None
    _logger = None

    def __init__(self, app_window):
        self._exit_event = Event()
        self._app_window = app_window
        self._logger = logging.getLogger('ulauncher')
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)
        signal.signal(signal.SIGHUP, self._reload_configs)

    def _reload_configs(self, *args):
        self._logger.info('Received SIGHUP. Reloading configs')
        self._app_window.init_theme()

    def killed(self):
        """
        :rtype: bool
        """
        return self._exit_event.is_set()

    def _exit_gracefully(self, signum, frame):
        self._exit_event.set()


def main():
    """
    Main function that starts everything
    """
    if is_wayland() and gdk_backend().lower() != 'x11' and not is_wayland_compatibility_on():
        warn = """
                    [!]
        Looks like you are in Wayland session
        Please run Ulauncher with env var
        GDK_BACKEND set to 'x11' like this:

        GDK_BACKEND=x11 ulauncher
        """
        print(warn, file=sys.stderr)
        sys.exit(1)

    # start DBus loop
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    instance = bus.request_name(DBUS_SERVICE)

    if instance != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        toggle_window = dbus.SessionBus().get_object(DBUS_SERVICE, DBUS_PATH).get_dbus_method("toggle_window")
        toggle_window()
        return

    _create_dirs()

    options = get_options()
    setup_logging(options)
    logger = logging.getLogger('ulauncher')
    logger.info('Ulauncher version %s' % get_version())
    logger.info("GTK+ %s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()))
    logger.info("Is Wayland: %s" % is_wayland())
    logger.info("Wayland compatibility: %s" % ('on' if is_wayland_compatibility_on() else 'off'))

    # log uncaught exceptions
    def except_hook(exctype, value, tb):
        logger.error("Uncaught exception", exc_info=(exctype, value, tb))

    sys.excepthook = except_hook

    window = UlauncherWindow.get_instance()
    UlauncherDbusService(window)
    if not options.hide_window:
        window.show()

    if Settings.get_instance().get_property('show-indicator-icon'):
        AppIndicator.get_instance().show()

    # workaround to make Ctrl+C quiting the app
    signal_handler = SignalHandler(window)
    gtk_thread = run_async(Gtk.main)()
    try:
        while gtk_thread.is_alive() and not signal_handler.killed():
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.warn('On KeyboardInterrupt')
    finally:
        Gtk.main_quit()
