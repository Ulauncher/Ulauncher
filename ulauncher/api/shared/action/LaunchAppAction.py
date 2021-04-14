import logging
import pipes
import subprocess
import shlex

from ulauncher.utils.desktop.reader import read_desktop_file
from ulauncher.utils.Settings import Settings
from ulauncher.api.shared.action.BaseAction import BaseAction

logger = logging.getLogger(__name__)
settings = Settings.get_instance()


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
        command = app.get_string('Exec')
        
        terminal_exec = settings.get_property('terminal-command')
        if app.get_boolean('Terminal') and terminal_exec and command:
            logger.info('Run command %s (%s) in preferred terminal (%s)', command, self.filename, terminal_exec)
            subprocess.Popen(terminal_exec.split() + [pipes.quote(command)])
        else:
            logger.info('Run application %s (%s)', app.get_name(), self.filename)
            try:
                if (command.startswith("pkexec")):
                    subprocess.Popen(
                        args=shlex.split('sh -c "'+command+'"'),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True
                    )
                else:
                    app.launch()
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)
