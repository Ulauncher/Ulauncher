import logging
import os
import signal

from ulauncher.gi import GLib

logger = logging.getLogger(__name__)
v5_service_name = "net.launchpad.ulauncher"


def kill_ulauncher_v5() -> None:
    """
    Kills the Ulauncher v5 instance if it is running.

    The purpose of this is to ensure that v5 is not running when v6 is started. The two share the
    settings, the extension preferences and the extensions, so running both corrupts the config and
    starts every extension twice. v5 refuses to start while v6 is running, so only v6 kills.
    See https://github.com/Ulauncher/Ulauncher/issues/1093 for more.
    """
    # Find the Ulauncher v5 service on the session bus
    from ulauncher.utils.dbus import get_app_pid

    try:
        pid = get_app_pid(v5_service_name)
    except GLib.Error:
        # No session bus to ask, so there is nothing running to kill either
        return

    if not pid:
        return

    logger.info("Ulauncher v5 is running with PID: %s. Killing...", pid)

    try:
        os.kill(pid, signal.SIGTERM)
        logger.info("PID: %s killed.", pid)
    except ProcessLookupError:
        logger.info("Process with PID %s not found (already dead?).", pid)
    except (OSError, ValueError) as ex:
        logger.info("Failed to kill process: %s", ex)
