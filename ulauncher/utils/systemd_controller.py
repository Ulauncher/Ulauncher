from __future__ import annotations

import logging
import subprocess
from shutil import which

from ulauncher.data import Err, Fallible, Ok

logger = logging.getLogger(__name__)


def systemctl_run(*args: str) -> Fallible[str, str]:
    """Run a systemctl --user command. Err carries the failure detail, already logged here."""
    try:
        result = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, check=True)
        return Ok(result.stdout.rstrip())
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip() or f"exit code {e.returncode}"
        logger.warning("systemctl --user %s failed (%s): %s", " ".join(args), e.returncode, detail)
        return Err(detail)
    except OSError as e:
        logger.warning("systemctl --user %s failed: %s", " ".join(args), e)
        return Err(str(e))


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

    def status(self) -> Fallible[SystemdUnitStatus, str]:
        """Snapshot of unit state from a single `systemctl show` call (or empty if not supported).

        Err when the reload or query failed, so callers cannot mistake an unknown
        or stale state for a current one.
        """
        if not self.supported:
            return Ok(SystemdUnitStatus([]))
        result = systemctl_run("show", self._unit)
        if isinstance(result, Err):
            return result
        if "NeedDaemonReload=yes" in result.value:
            logger.info("Reloading systemd daemon")
            reload_result = systemctl_run("daemon-reload")
            if isinstance(reload_result, Err):
                return reload_result
            result = systemctl_run("show", self._unit)
            if isinstance(result, Err):
                return result
        return Ok(SystemdUnitStatus(result.value.splitlines()))

    def restart(self) -> None:
        if self.supported:
            systemctl_run("restart", self._unit)

    def stop(self) -> None:
        if self.supported:
            systemctl_run("stop", self._unit)

    def toggle(self, status: bool) -> None:
        """Enable or disable unit"""
        if status:
            result = self.status()
            if isinstance(result, Err):
                msg = f"Could not query autostart status: {result.error}"
                raise OSError(msg)
            if not result.value.can_start:
                msg = "Autostart is not allowed"
                raise OSError(msg)

        systemctl_run("reenable" if status else "disable", self._unit)
