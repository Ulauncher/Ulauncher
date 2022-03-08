import sys
import signal
import logging
from functools import partial
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports,unused-import
# This module also starts the dbus main loop and handles if the app is already running.
from ulauncher.utils.dbus import UlauncherDbusService
# This xinit import must happen before any GUI libraries are initialized.
import ulauncher.utils.xinit  # noqa: F401
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, GLib
from ulauncher.config import API_VERSION, VERSION, get_options
from ulauncher.utils.wayland import is_wayland, is_wayland_compatibility_on
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.utils.Settings import Settings
from ulauncher.utils.setup_logging import setup_logging

logger = logging.getLogger('ulauncher')


def reload_config(win):
    logger.info("Reloading config")
    win.init_theme()


def graceful_exit(data):
    logger.info("Exiting gracefully nesting level %s: %s", Gtk.main_level(), data)
    # ExtensionServer.get_instance().stop()
    # Gtk.main_quit()
    sys.exit(0)


def main():
    """
    Main function that starts everything
    """

    options = get_options()
    setup_logging(options)
    logger.info('Ulauncher version %s', VERSION)
    logger.info('Extension API version %s', API_VERSION)
    logger.info("GTK+ %s.%s.%s", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    logger.info("Is Wayland: %s", is_wayland())
    logger.info("Wayland compatibility: %s", ('on' if is_wayland_compatibility_on() else 'off'))
    if (Gtk.get_major_version(), Gtk.get_minor_version()) < (3, 22):
        logger.error("Ulauncher requires GTK+ version 3.22 or newer. Please upgrade your GTK version.")
    if options.no_window_shadow:
        logger.warning("The --no-window-shadow argument has been moved to a user setting")
    if options.hide_window:
        # Ulauncher's "Launch at Login" is now implemented with systemd, but originally
        # it was implemented using XDG autostart. To prevent files created the old way
        # from starting a second Ulauncher background process we have to make sure the
        # --no-window flag prevents the app from starting.
        sys.exit("The --hide-window argument has been renamed to --no-window")

    # log uncaught exceptions
    def except_hook(exctype, value, tb):
        logger.error("Uncaught exception", exc_info=(exctype, value, tb))

    sys.excepthook = except_hook

    window = UlauncherWindow.get_instance()
    UlauncherDbusService(window)
    if not options.no_window:
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
