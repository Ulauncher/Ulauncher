import sys
import argparse
import signal
import logging
from functools import partial
# This xinit import must happen before any GUI libraries are initialized.
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports,unused-import
import ulauncher.utils.xinit  # noqa: F401
import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio, GLib, Gtk
from ulauncher.config import API_VERSION, VERSION, get_options
from ulauncher.utils.environment import DESKTOP_NAME, DISTRO, XDG_SESSION_TYPE, IS_X11_COMPATIBLE
from ulauncher.utils.setup_logging import setup_logging


class UlauncherApp(Gtk.Application):
    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    window = None

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="net.launchpad.ulauncher",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.connect("startup", self.setup)  # runs only once on the main instance

    def setup(self, _):
        self.hold()  # Keep the app running even without a window
        # These modules are very heavy, so we don't want to load them in the remote
        # pylint: disable=import-outside-toplevel
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        self.window = UlauncherWindow.get_instance()
        self.window.set_application(self)

    def do_activate(self, *args, **kwargs):
        self.window.show_window()

    def do_command_line(self, *args, **kwargs):
        # This is where we handle "--no-window" which we need to get from the remote call
        # All other aguments are persistent and handled in config.get_options()
        parser = argparse.ArgumentParser(prog='gui')
        parser.add_argument("--no-window", action="store_true")
        args, _ = parser.parse_known_args(args[0].get_arguments()[1:])

        if not args.no_window:
            self.activate()

        return 0


logger = logging.getLogger('ulauncher')


def reload_config(app):
    logger.info("Reloading config")
    app.window.init_theme()


def main():
    """
    Main function that starts everything
    """

    options = get_options()
    setup_logging(options)
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
        partial(reload_config, app),
        None
    )
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, app.quit)

    try:
        app.run(sys.argv)
    except KeyboardInterrupt:
        logger.warning('On KeyboardInterrupt')
