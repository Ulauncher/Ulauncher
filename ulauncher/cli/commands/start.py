from __future__ import annotations

import contextlib
import logging
import os
import sys
from types import TracebackType

from ulauncher.cli import CLIArguments


def run(_: CLIArguments) -> int:
    from ulauncher import init_helpers

    init_helpers.init_x11_threads()

    from ulauncher import api_version, version
    from ulauncher.ui.app import UlauncherApp  # noqa: TID251
    from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME, DISTRO, IS_X11_COMPATIBLE, XDG_SESSION_TYPE
    from ulauncher.utils.migrate import v5_to_v6
    from ulauncher.utils.v5_killer import kill_ulauncher_v5

    gtk_version = UlauncherApp.get_gtk_version()
    if gtk_version < (3, 22, 0):
        print("Ulauncher requires GTK+ version 3.22 or newer. Please upgrade your GTK version.")  # noqa: T201
        return 1

    logger = logging.getLogger(__name__)

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

    # Perf-test probe (see UlauncherWindow.on_initial_draw): when ULAUNCHER_PERF_START_BOOTTIME
    # is set, schedule the launcher to open as soon as the main loop is idle so the probe can
    # measure cold-start to first input. Without this, `ulauncher start` would register as a
    # daemon and idle until an external D-Bus activation arrived.
    if os.environ.get("ULAUNCHER_PERF_START_BOOTTIME"):
        from ulauncher.utils import scheduling

        scheduling.run_when_idle(app.show_launcher)

    with contextlib.suppress(KeyboardInterrupt):
        app.start(activate=False)

    return 0
