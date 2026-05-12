from __future__ import annotations

import contextlib
import logging
import sys
from types import TracebackType

from ulauncher import api_version, cli, init_helpers, version


def main() -> None:  # noqa: PLR0915
    """
    Main function that starts everything
    """
    cli_args = cli.get_args()  # sys.exit() here for --help / --version
    in_cli_mode = hasattr(cli_args, "handler")

    init_helpers.ensure_runtime_dirs()

    if in_cli_mode:
        init_helpers.configure_logging(verbose=cli_args.verbose, use_app_logging=False)
        sys.exit(0 if cli_args.handler(cli_args) else 1)

    init_helpers.init_x11_threads()

    from ulauncher.ui.app import UlauncherApp  # noqa: TID251
    from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME, DISTRO, IS_X11_COMPATIBLE, XDG_SESSION_TYPE
    from ulauncher.utils.migrate import v5_to_v6
    from ulauncher.utils.v5_killer import kill_ulauncher_v5

    gtk_version = UlauncherApp.get_gtk_version()
    if gtk_version < (3, 22, 0):
        print("Ulauncher requires GTK+ version 3.22 or newer. Please upgrade your GTK version.")  # noqa: T201
        sys.exit(2)

    if cli_args.hide_window:
        # Ulauncher's "Launch at Login" is now implemented with systemd, but originally
        # it was implemented using XDG autostart. To prevent files created the old way
        # from starting a second Ulauncher background process we have to make sure the
        # --daemon flag prevents the app from starting.
        print("The --hide-window argument has been renamed to --daemon")  # noqa: T201
        sys.exit(2)
    if cli_args.no_window:
        # --hide-window was renamed to --no-window for a while in v6 beta (never released)
        print("The --no-window argument has been renamed to --daemon")  # noqa: T201
        sys.exit(2)
    if cli_args.dev:
        print("The --dev argument has been removed (use --verbose instead)")  # noqa: T201
        sys.exit(2)

    init_helpers.configure_logging(verbose=cli_args.verbose, use_app_logging=True)

    # Logger for actual use in this file
    logger = logging.getLogger(__name__)

    # log uncaught exceptions
    def except_hook(exctype: type[BaseException], exception: BaseException, traceback: TracebackType | None) -> None:
        logger.error("Uncaught exception", exc_info=(exctype, exception, traceback))

    sys.excepthook = except_hook

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

    logger.info("Ulauncher version %s", version)
    logger.info("Extension API version %s", api_version)
    logger.info("GTK+ %s.%s.%s", *gtk_version)
    logger.info("PyGObject+ %i.%i.%i", *UlauncherApp.get_pygobject_version())
    if cli_args.no_extensions:
        logger.warning("The --no-extensions argument has been removed in Ulauncher v6")
    if cli_args.no_window_shadow:
        logger.warning("The --no-window-shadow argument has been removed in Ulauncher v6")

    if XDG_SESSION_TYPE != "X11":
        from ulauncher.ui.helpers import layer_shell  # noqa: TID251

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

    # Ensure that Ulauncher v5 is not running
    # TODO: Remove this 4-6 months after v6 release
    # Import here because of the dependency on the logger setup
    kill_ulauncher_v5()

    # Migrate user data to v6 compatible
    v5_to_v6()

    app = UlauncherApp()

    with contextlib.suppress(KeyboardInterrupt):
        app.start(activate=not cli_args.daemon)
