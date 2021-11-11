import logging
import os
import re
import shlex
import shutil
from pathlib import Path
import gi

gi.require_version("GLib", "2.0")
# pylint: disable=wrong-import-position
from gi.repository import GLib

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
            env = dict(os.environ.items())
            # Make sure GDK apps aren't forced to use x11 on wayland due to ulauncher's need to run
            # under X11 for proper centering.
            env.pop("GDK_BACKEND", None)
            if app.get_boolean('Terminal'):
                if terminal_exec:
                    logger.info('Will run command in preferred terminal (%s)', terminal_exec)
                    sanitized_exec = terminal_exec + [sanitized_exec]
                else:
                    sanitized_exec = ['gtk-launch', app_id]
            else:
                sanitized_exec = shlex.split(sanitized_exec)
            if hasSystemdRun and not app.get_boolean('X-Ulauncher-Inherit-Scope'):
                setenv = ["--setenv={}={}".format(k, v) for k, v in env.items()]
                sanitized_exec = [
                    'systemd-run',
                    '--user',
                    '--remain-after-exit'
                ] + setenv + sanitized_exec

            try:
                logger.info('Run application %s (%s) Exec %s', app.get_name(), self.filename, exec)
                envp = ["{}={}".format(k, v) for k, v in env.items()]
                GLib.spawn_async(
                    argv=sanitized_exec,
                    envp=envp,
                    flags=GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP | GLib.SpawnFlags.SEARCH_PATH,
                    # setsid is really only needed if systemd-run is missing, but doesn't hurt to have.
                    child_setup=os.setsid
                )
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)
