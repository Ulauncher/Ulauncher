import logging
import subprocess
import re
import shlex
import shutil
from pathlib import Path

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
        app_id = Path(self.filename).with_suffix('').stem
        exec = app.get_string('Exec')
        if not exec:
            logger.error("No command to run %s", self.filename)
        else:
            # strip field codes %f, %F, %u, %U, etc
            sanitized_exec = re.sub(r'\%[uUfFdDnNickvm]', '', exec).rstrip()
            terminal_exec = shlex.split(settings.get_property('terminal-command'))
            if app.get_boolean('Terminal'):
                if terminal_exec:
                    logger.info('Will run command in preferred terminal (%s)', terminal_exec)
                    sanitized_exec = terminal_exec + [sanitized_exec]
                else:
                    sanitized_exec = ['gtk-launch', app_id]
            else:
                sanitized_exec = shlex.split(sanitized_exec)
            if hasSystemdRun:
                # Escape the Ulauncher cgroup, so this process isn't considered a child process of Ulauncher
                # and doesn't die if Ulauncher dies/crashed/is terminated
                # The slice name is super sensitive and must not contain invalid characters like space
                # or trailing or leading hyphens
                sanitized_app = re.sub(r'(^-*|[^\w^\-^\.]|-*$)', '', app_id)
                sanitized_exec = ['systemd-run', '--user', '--scope', '--slice=app-{}'.format(sanitized_app)] + sanitized_exec
            try:
                logger.info('Run application %s (%s) Exec %s', app.get_name(), self.filename, exec)
                # Start_new_session is only needed if systemd-run is missing
                subprocess.Popen(sanitized_exec, start_new_session=True)
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)
