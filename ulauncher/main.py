import sys
import signal
import logging
from functools import partial
# This xinit import must happen before any GUI libraries are initialized.
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports,unused-import
import ulauncher.utils.xinit  # noqa: F401
import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib, Gtk
from ulauncher.config import API_VERSION, STATE_DIR, VERSION, get_options
from ulauncher.utils.environment import DESKTOP_NAME, DISTRO, XDG_SESSION_TYPE, IS_X11_COMPATIBLE
from ulauncher.utils.logging import ColoredFormatter, log_format
from ulauncher.ui.UlauncherApp import UlauncherApp


def reload_config(app, logger):
    logger.info("Reloading config")
    app.window.init_theme()


def main():
    """
    Main function that starts everything
    """
    options = get_options()

    # Set up global logging for stdout and file
    root_log_handler = logging.getLogger()
    root_log_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if options.verbose else logging.WARNING)
    stream_handler.setFormatter(ColoredFormatter(log_format))
    root_log_handler.addHandler(stream_handler)

    file_handler = logging.FileHandler(f"{STATE_DIR}/last.log", mode='w+')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    root_log_handler.addHandler(file_handler)

    # Logger for actual use in this file
    logger = logging.getLogger('ulauncher')

    logger.info('Ulauncher version %s', VERSION)
    logger.info('Extension API version %s', API_VERSION)
    logger.info("GTK+ %s.%s.%s", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    logger.info("Desktop: %s (%s) on %s", DESKTOP_NAME, XDG_SESSION_TYPE, DISTRO)

    if XDG_SESSION_TYPE != "X11":
        logger.info("X11 backend: %s", ('Yes' if IS_X11_COMPATIBLE else 'No'))
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

    app = UlauncherApp()

    GLib.unix_signal_add(
        GLib.PRIORITY_DEFAULT,
        signal.SIGHUP,
        partial(reload_config, app, logger),
        None
    )
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, app.quit)

    try:
        app.run(sys.argv)
    except KeyboardInterrupt:
        logger.warning('On KeyboardInterrupt')
