import sys
import signal
import logging
from functools import partial

# This xinit import must happen before any GUI libraries are initialized.
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports,unused-import
import ulauncher.utils.xinit  # noqa: F401
import gi
from gi.repository import GLib, Gtk
from ulauncher.config import API_VERSION, PATHS, VERSION, get_options
from ulauncher.utils.migrate import v5_to_v6
from ulauncher.utils.environment import DESKTOP_NAME, DISTRO, XDG_SESSION_TYPE, IS_X11_COMPATIBLE
from ulauncher.utils.logging_color_formatter import ColoredFormatter
from ulauncher.ui.UlauncherApp import UlauncherApp


def reload_config(app, logger):
    logger.info("Reloading config")
    app.window.apply_theme()


def main(is_dev=False):
    """
    Main function that starts everything
    """
    options = get_options()
    if (Gtk.get_major_version(), Gtk.get_minor_version()) < (3, 22):
        print("Ulauncher requires GTK+ version 3.22 or newer. Please upgrade your GTK version.")
        sys.exit(2)
    if options.hide_window:
        # Ulauncher's "Launch at Login" is now implemented with systemd, but originally
        # it was implemented using XDG autostart. To prevent files created the old way
        # from starting a second Ulauncher background process we have to make sure the
        # --no-window flag prevents the app from starting.
        print("The --hide-window argument has been renamed to --no-window")
        sys.exit(2)

    if is_dev:
        # Ensure preferences UI is built
        # pylint: disable=import-outside-toplevel
        from setuptools import sandbox

        sandbox.run_setup("setup.py", ["build_prefs"])

    # Set up global logging for stdout and file
    file_handler = logging.FileHandler(f"{PATHS.STATE}/last.log", mode="w+")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if options.verbose else logging.WARNING)
    stream_handler.setFormatter(ColoredFormatter())

    logging.root.handlers = []
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(message)s | %(module)s.%(funcName)s():%(lineno)s",
        handlers=[file_handler, stream_handler],
    )

    # Logger for actual use in this file
    logger = logging.getLogger()

    logger.info("Ulauncher version %s", VERSION)
    logger.info("Extension API version %s", API_VERSION)
    logger.info("GTK+ %s.%s.%s", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    logger.info("PyGObject+ %i.%i.%i", *gi.version_info)

    logger.info("Desktop: %s (%s) on %s", DESKTOP_NAME, XDG_SESSION_TYPE, DISTRO)

    if XDG_SESSION_TYPE != "X11":
        logger.info("X11 backend: %s", ("Yes" if IS_X11_COMPATIBLE else "No"))
    if options.no_extensions:
        logger.warning("The --no-extensions argument has been removed in Ulauncher v6")
    if options.no_window_shadow:
        logger.warning("The --no-window-shadow argument has been removed in Ulauncher v6")

    # log uncaught exceptions
    def except_hook(exctype, value, tb):
        logger.error("Uncaught exception", exc_info=(exctype, value, tb))

    sys.excepthook = except_hook

    # Migrate user data to v6 compatible
    v5_to_v6()

    app = UlauncherApp.get_instance()

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGHUP, partial(reload_config, app, logger), None)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, app.quit)

    try:
        app.run(sys.argv)
    except KeyboardInterrupt:
        pass
