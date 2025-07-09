import logging
from shutil import which
from subprocess import check_output

logger = logging.getLogger()


def systemctl_run(*args: str) -> str:
    try:
        return check_output(["systemctl", "--user", *args]).decode("utf-8").rstrip()
    except Exception:  # noqa: BLE001
        return ""


class SystemdController:
    def __init__(self, unit: str) -> None:
        self.unit = unit
        self.supported = bool(which("systemctl"))

    def can_start(self) -> bool:
        """
        :returns: True if unit exists and can start
        """
        if not self.supported:
            return False
        status = systemctl_run("show", self.unit)
        if "NeedDaemonReload=yes" in status:
            logger.info("Reloading systemd daemon")
            systemctl_run("daemon-reload")
            status = systemctl_run("show", self.unit)
        return "CanStart=yes" in status

    def is_active(self) -> bool:
        """
        :returns: True if unit is currently running
        """
        return self.supported and systemctl_run("is-active", self.unit) == "active"

    def is_enabled(self) -> bool:
        """
        :returns: True if unit is set to start automatically
        """
        return self.supported and systemctl_run("is-enabled", self.unit) == "enabled"

    def restart(self) -> None:
        if self.supported:
            systemctl_run("restart", self.unit)

    def stop(self) -> None:
        if self.supported:
            systemctl_run("stop", self.unit)

    def toggle(self, status: bool) -> None:
        """
        Enable or disable unit
        """
        if status and not self.can_start():
            msg = "Autostart is not allowed"
            raise OSError(msg)

        systemctl_run("reenable" if status else "disable", self.unit)
