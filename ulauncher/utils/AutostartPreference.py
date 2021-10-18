import shutil
import subprocess


def systemctl_unit_run(*args):
    try:
        return subprocess.check_output(["systemctl", "--user"] + list(args) + ["ulauncher"]).decode('utf-8').rstrip()
    except Exception:
        return False


class AutostartPreference:
    def is_allowed(self):
        """
        :returns: True if autostart can be controlled by Ulauncher
        """
        return bool(shutil.which("systemctl")) and 'ExecStart' in systemctl_unit_run("cat")

    def is_enabled(self):
        """
        :returns: True if Ulauncher is set to start automatically
        """
        return self.is_allowed() and systemctl_unit_run("is-enabled") == 'enabled'

    def switch(self, status):
        """
        Enable or disable Ulauncher systemd unit

        :param bool status:
        """
        if not self.is_allowed():
            raise 'Autostart is not allowed'

        systemctl_unit_run("reenable" if status else "disable")
