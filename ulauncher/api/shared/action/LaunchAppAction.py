import logging
import subprocess
import re
import shlex
import shutil

from ulauncher.utils.desktop.reader import read_desktop_file
from ulauncher.utils.Settings import Settings
from ulauncher.api.shared.action.BaseAction import BaseAction

logger = logging.getLogger(__name__)
settings = Settings.get_instance()
hasSystemdRun = bool(shutil.which("systemd-run"))


class LaunchAppAction(BaseAction):
    """
    Launches app by given `.desktop` file path

    :param str filename: path to .desktop file
    """

    def __init__(self, filename):
        self.filename = filename

    def keep_app_open(self):
        return False

    def run(self):
        app = read_desktop_file(self.filename)
        exec = app.get_string('Exec')
        if not exec:
            logger.error("No command to run %s", self.filename)
        else:
            # strip field codes %f, %F, %u, %U, etc
            sanitized_exec = re.sub(r'\%[uUfFdDnNickvm]', '', exec).rstrip()
            terminal_exec = shlex.split(settings.get_property('terminal-command'))
            if app.get_boolean('Terminal') and terminal_exec:
                logger.info('Will run command in preferred terminal (%s)', terminal_exec)
                sanitized_exec = terminal_exec + [sanitized_exec]
            else:
                sanitized_exec = shlex.split(sanitized_exec)
            if hasSystemdRun:
                # Escape the Ulauncher cgroup, so this process isn't considered a child process of Ulauncher
                # and doesn't die if Ulauncher dies/crashed/is terminated
                sanitized_app = re.sub(r'[\W]', '-', app.get_name())
                sanitized_exec = ['systemd-run', '--user', '--scope', f'--slice={sanitized_app}.slice'] + sanitized_exec
            try:
                logger.info('Run application %s (%s) Exec %s', app.get_name(), self.filename, exec)
                # Start_new_session is only needed if systemd-run is missing
                subprocess.Popen(sanitized_exec, start_new_session=True)
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)
