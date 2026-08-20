import time
import os
import logging
import subprocess
import tempfile
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.decorator.run_async import run_async

logger = logging.getLogger(__name__)


class RunScriptAction(BaseAction):
    """
    Runs a user script

    :param str script: script content
    :param str args: arguments, passed to the shell as written
    """

    def __init__(self, script, args=None):
        self.script = script
        self.args = args

    def get_command(self, file_name):
        return f'{file_name} {self.args}' if self.args else file_name

    def run(self):
        file = tempfile.NamedTemporaryFile(prefix='ulauncher_RunScript_', delete=False)

        try:
            file.write(self.script.encode())
        except Exception:
            file.close()
            raise
        else:
            file.close()

        try:
            os.chmod(file.name, 0o777)
            logger.debug('Running a script from %s', file.name)
            subprocess.Popen([self.get_command(file.name)],
                             shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            self.remove_temp_file(file.name)
        except Exception:
            self.remove_temp_file(file.name)
            raise

    @run_async(daemon=True)
    def remove_temp_file(self, filename: str) -> None:
        time.sleep(1)  # wait just a bit, because Popen runs file asynchronously
        logger.debug('Deleting a temporary file %s', filename)
        os.remove(filename)
