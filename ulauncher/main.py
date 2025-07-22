from __future__ import annotations

import contextlib
import logging
import os
import signal
import sys
from types import TracebackType

import gi
from gi.repository import GLib, Gtk

import ulauncher.utils.xinit  # noqa: F401 - must import this before any GUI libraries are initialized
from ulauncher import api_version, paths, version
from ulauncher.cli import get_cli_args
from ulauncher.ui import layer_shell
from ulauncher.ui.ulauncher_app import UlauncherApp
from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME, DISTRO, IS_X11_COMPATIBLE, XDG_SESSION_TYPE
from ulauncher.utils.logging_color_formatter import ColoredFormatter
from ulauncher.utils.migrate import v5_to_v6


def main() -> None:  # noqa: PLR0915
    """
    Main function that starts everything
    """
    if not os.path.exists(paths.ASSETS):
        raise OSError(paths.ASSETS)

    os.makedirs(paths.CONFIG, exist_ok=True)
    os.makedirs(paths.STATE, exist_ok=True)
    os.makedirs(paths.USER_EXTENSIONS, exist_ok=True)
    os.makedirs(paths.EXTENSIONS_CONFIG, exist_ok=True)
    os.makedirs(paths.USER_THEMES, exist_ok=True)

    cli_args = get_cli_args()

    if (Gtk.get_major_version(), Gtk.get_minor_version()) < (3, 22):
        print("Ulauncher requires GTK+ version 3.22 or newer. Please upgrade your GTK version.")  # noqa: T201
        sys.exit(2)
    if cli_args.hide_window:
        # Ulauncher's "Launch at Login" is now implemented with systemd, but originally
        # it was implemented using XDG autostart. To prevent files created the old way
        # from starting a second Ulauncher background process we have to make sure the
        # --daemon flag prevents the app from starting.
        print("The --hide-window argument has been renamed to --daemon")  # noqa: T201
        sys.exit(2)

    # Set up global logging for stdout and file
    file_handler = logging.FileHandler(f"{paths.STATE}/last.log", mode="w+")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if cli_args.verbose else logging.WARNING)
    stream_handler.setFormatter(ColoredFormatter())

    logging.root.handlers = []
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(message)s | %(module)s.%(funcName)s():%(lineno)s",
        handlers=[file_handler, stream_handler],
    )

    # Logger for actual use in this file
    logger = logging.getLogger()

    logger.info("Ulauncher version %s", version)
    logger.info("Extension API version %s", api_version)
    logger.info("GTK+ %s.%s.%s", Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    logger.info("PyGObject+ %i.%i.%i", *gi.version_info)  # type: ignore[attr-defined]

    logger.info("Desktop: %s (%s) on %s", DESKTOP_NAME, XDG_SESSION_TYPE, DISTRO)
    if "-" in version:
        logger.warning(
            "\n"
            "\n╔═════════════════════════════════════════════════════════════════════════════╗"
            "\n║                  YOU ARE RUNNING A PRE-RELEASE of ULAUNCHER.                ║"
            "\n║ Please do not report extension API support warnings to extension developers ║"
            "\n║ We are still in the process of developing and documenting these features    ║"
            "\n╚═════════════════════════════════════════════════════════════════════════════╝"
            "\n\n"
        )

    if XDG_SESSION_TYPE != "X11":
        layer_shell_supported = layer_shell.is_supported()
        logger.info("Layer shell: %s", ("Yes" if layer_shell_supported else "No"))
        if not layer_shell_supported and DESKTOP_ID == "PLASMA":
            logger.warning(
                "\n"
                "\n╔═════════════════════════════════════════════════════════════════════════════╗"
                "\n║ Plasma Desktop needs Layer Shell to render Ulauncher correctly on Wayland.  ║"
                "\n║  See https://github.com/Ulauncher/Ulauncher/discussions/1501 for details.   ║"
                "\n╚═════════════════════════════════════════════════════════════════════════════╝"
                "\n\n"
            )
        logger.info("X11 backend: %s", ("Yes" if IS_X11_COMPATIBLE else "No"))
    if cli_args.no_extensions:
        logger.warning("The --no-extensions argument has been removed in Ulauncher v6")
    if cli_args.no_window_shadow:
        logger.warning("The --no-window-shadow argument has been removed in Ulauncher v6")

    # log uncaught exceptions
    def except_hook(exctype: type[BaseException], exception: BaseException, traceback: TracebackType | None) -> None:
        logger.error("Uncaught exception", exc_info=(exctype, exception, traceback))

    sys.excepthook = except_hook

    # Ensure that Ulauncher v5 is not running
    # TODO: Remove this 4-6 months after v6 release
    # Import here because of the dependency on the logger setup
    from ulauncher.utils.v5_killer import kill_ulauncher_v5

    kill_ulauncher_v5()

    # Migrate user data to v6 compatible
    v5_to_v6()

    app = UlauncherApp()

    def handler() -> bool:
        app.quit()
        return False

    GLib.unix_signal_add(priority=GLib.PRIORITY_DEFAULT, signum=signal.SIGTERM, handler=handler)

    with contextlib.suppress(KeyboardInterrupt):
        app.run(sys.argv)
