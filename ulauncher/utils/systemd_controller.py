import logging
from shutil import which
from subprocess import check_output, run

logger = logging.getLogger()


def systemctl_unit_run(*args):
    try:
        return check_output(["systemctl", "--user"] + list(args) + ["ulauncher"]).decode("utf-8").rstrip()
    except Exception:
        return False


class UlauncherSystemdController:
    def is_allowed(self):
        """
        :returns: True if autostart can be controlled by Ulauncher
        """
        if not which("systemctl"):
            logger.info("Need systemd to use Ulauncher 'Launch at Login'")
            return False
        status = systemctl_unit_run("show")
        if "NeedDaemonReload=yes" in status:
            logger.info("Reloading systemd daemon")
            run(["systemctl", "--user", "daemon-reload"], check=True)
            status = systemctl_unit_run("show")
        return "CanStart=yes" in status

    def is_enabled(self):
        """
        :returns: True if Ulauncher is set to start automatically
        """
        return self.is_allowed() and systemctl_unit_run("is-enabled") == "enabled"

    def switch(self, status):
        """
        Enable or disable Ulauncher systemd unit

        :param bool status:
        """
        if not self.is_allowed():
            raise OSError("Autostart is not allowed")

        systemctl_unit_run("reenable" if status else "disable")
