import logging
import os
import signal

from ulauncher import first_v6_run

logger = logging.getLogger()
v5_service_name = "net.launchpad.ulauncher"


def kill_ulauncher_v5() -> None:
    """
    Kills the Ulauncher v5 instance if it is running.

    The purpose of this is to ensure that v5 is not running when v6 is started.
    This check is necessary only on the first run of v6 during the upgrade.
    See https://github.com/Ulauncher/Ulauncher/issues/1093 for more.
    """
    if not first_v6_run:
        return

    # Find the Ulauncher v5 service on the session bus
    from ulauncher.utils.dbus import get_app_pid

    pid = get_app_pid(v5_service_name)

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
