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

    try:
        import dbus
    except ImportError:
        logger.info("DBus is not available. Cannot check for Ulauncher v5 instance.")
        return

    bus = dbus.SessionBus()
    try:
        # Find the Ulauncher v5 service on the session bus
        dbus_proxy = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
        dbus_iface = dbus.Interface(dbus_proxy, dbus_interface="org.freedesktop.DBus")
        names = dbus_iface.ListNames()
        if v5_service_name not in names:
            return

        # Ask for PIDs owning this connection
        owner = dbus_iface.GetNameOwner(v5_service_name)
        pid = dbus_iface.GetConnectionUnixProcessID(owner)
        logger.info("Ulauncher v5 is running with PID: %s. Killing...", pid)

        try:
            os.kill(pid, signal.SIGTERM)
            logger.info("PID: %s killed.", pid)
        except ProcessLookupError:
            logger.info("Process with PID %s not found (already dead?).", pid)
        except Exception as ex:  # noqa: BLE001
            logger.info("Failed to kill process: %s", ex)
            return
    except dbus.DBusException as ex:
        logger.exception("Failed to communicate with DBus: %s", ex.get_dbus_message())
        return
