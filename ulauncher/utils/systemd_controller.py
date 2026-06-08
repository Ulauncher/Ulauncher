from __future__ import annotations

import logging
import subprocess
from shutil import which

logger = logging.getLogger(__name__)


def systemctl_run(*args: str) -> str:
    try:
        return subprocess.check_output(["systemctl", "--user", *args]).decode("utf-8").rstrip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return ""


class SystemdUnitStatus:
    """Point-in-time snapshot of a unit's `systemctl show` properties."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    @property
    def can_start(self) -> bool:
        """Returns True if unit exists and can start"""
        return "CanStart=yes" in self._lines

    @property
    def is_active(self) -> bool:
        """Returns True if unit is currently running"""
        return "ActiveState=active" in self._lines

    @property
    def is_enabled(self) -> bool:
        """Returns True if unit is set to start automatically"""
        return "UnitFileState=enabled" in self._lines


class SystemdController:
    def __init__(self, unit: str) -> None:
        self._unit = unit
        self.supported = bool(which("systemctl"))

    def status(self) -> SystemdUnitStatus:
        """Snapshot of unit state from a single `systemctl show` call (or empty if not supported)"""
        if not self.supported:
            return SystemdUnitStatus([])
        status = systemctl_run("show", self._unit)
        if "NeedDaemonReload=yes" in status:
            logger.info("Reloading systemd daemon")
            systemctl_run("daemon-reload")
            status = systemctl_run("show", self._unit)
        return SystemdUnitStatus(status.splitlines())

    def restart(self) -> None:
        if self.supported:
            systemctl_run("restart", self._unit)

    def stop(self) -> None:
        if self.supported:
            systemctl_run("stop", self._unit)

    def toggle(self, status: bool) -> None:
        """Enable or disable unit"""
        if status and not self.status().can_start:
            msg = "Autostart is not allowed"
            raise OSError(msg)

        systemctl_run("reenable" if status else "disable", self._unit)
