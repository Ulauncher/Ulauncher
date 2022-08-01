import sys
import os
import signal
import logging
from functools import partial
from threading import Event
# This xinit import must happen before any GUI libraries are initialized.
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports,unused-import
import ulauncher.utils.xinit  # noqa: F401

import gi

# Fixes issue #488
sys.path.append('/usr/lib/python3.8/site-packages')

gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, GLib
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from ulauncher.config import get_version, get_options, CACHE_DIR, CONFIG_DIR, DATA_DIR
from ulauncher.utils.wayland import is_wayland, is_wayland_compatibility_on
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.utils.Settings import Settings
from ulauncher.utils.setup_logging import setup_logging
from ulauncher.api.version import api_version

logger = logging.getLogger('ulauncher')

DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'


def _create_dirs():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # make sure ~/.cache/ulauncher exists
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


class UlauncherDbusService(dbus.service.Object):
    def __init__(self, window):
        self.window = window
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus())
        super().__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_SERVICE)
    def toggle_window(self):
        self.window.toggle_window()


def reload_config(win):
    logger.info("Reloading config")
    win.init_theme()


def graceful_exit(data):
    logger.info("Exiting gracefully nesting level %s: %s", Gtk.main_level(), data)
    # ExtensionServer.get_instance().stop()
    # Gtk.main_quit()
    sys.exit(0)


# pylint: disable=too-few-public-methods
class SignalHandler:

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

    def _exit_gracefully(self, *args):
        self._exit_event.set()


def main():
    """
    Main function that starts everything
    """

    # start DBus loop
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    instance = bus.request_name(DBUS_SERVICE)

    if instance != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        print(
            "DBus name already taken. Ulauncher is probably backgrounded. Did you mean `ulauncher-toggle`?",
            file=sys.stderr
        )
        toggle_window = dbus.SessionBus().get_object(DBUS_SERVICE, DBUS_PATH).get_dbus_method("toggle_window")
        toggle_window()
        return

    _create_dirs()

    options = get_options()
    setup_logging(options)
    logger.info('Ulauncher version %s', get_version())
    logger.info('Extension API version %s', api_version)
    logger.info("GTK+ %s.%s.%s", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    logger.info("Is Wayland: %s", is_wayland())
    logger.info("Wayland compatibility: %s", ('on' if is_wayland_compatibility_on() else 'off'))

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

    GLib.unix_signal_add(
        GLib.PRIORITY_DEFAULT,
        signal.SIGHUP,
        partial(reload_config, window),
        None
    )
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, graceful_exit, None)

    try:
        Gtk.main()
    except KeyboardInterrupt:
        logger.warning('On KeyboardInterrupt')
