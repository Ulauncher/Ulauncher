import logging
from shutil import which
from subprocess import check_output

logger = logging.getLogger()


def systemctl_run(*args):
    try:
        return check_output(["systemctl", "--user", *args]).decode("utf-8").rstrip()
    except Exception:
        return False


class SystemdController:
    def __init__(self, unit: str):
        self.unit = unit

    def can_start(self):
        """
        :returns: True if unit exists and can start
        """
        if not which("systemctl"):
            logger.warning("systemctl command missing")
            return False
        status = systemctl_run("show", self.unit)
        if "NeedDaemonReload=yes" in status:
            logger.info("Reloading systemd daemon")
            systemctl_run("daemon-reload")
            status = systemctl_run("show", self.unit)
        return "CanStart=yes" in status

    def is_active(self):
        """
        :returns: True if unit is currently running
        """
        return systemctl_run("is-active", self.unit) == "active"

    def is_enabled(self):
        """
        :returns: True if unit is set to start automatically
        """
        return systemctl_run("is-enabled", self.unit) == "enabled"

    def restart(self):
        """
        :returns: Restart the service
        """
        return systemctl_run("restart", self.unit)

    def toggle(self, status):
        """
        Enable or disable unit

        :param bool status:
        """
        if not self.can_start():
            msg = "Autostart is not allowed"
            raise OSError(msg)

        systemctl_run("reenable" if status else "disable", self.unit)
