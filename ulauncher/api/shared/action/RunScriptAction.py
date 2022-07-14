import time
import os
import logging
import subprocess
import tempfile
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.decorator.run_async import run_async

logger = logging.getLogger()


class RunScriptAction(BaseAction):
    """
    Runs a user script

    :param str script: script content
    :param list args: arguments
    """

    def __init__(self, script, args=None):
        self.script = script
        self.args = args

    def run(self):
        file_path = f"{tempfile.gettempdir()}/ulauncher_run_script_{time.time()}"
        with open(file_path, 'w') as file:
            file.write(self.script)
        try:
            os.chmod(file_path, 0o777)
            logger.debug('Running a script from %s', file_path)
            output = subprocess.check_output([f"{file_path} {self.args}"], shell=True).decode('utf-8')
            logger.debug("Script action output:\n%s", output)
            self.remove_temp_file(file_path)
        except Exception:
            self.remove_temp_file(file_path)
            raise

    @run_async(daemon=True)
    def remove_temp_file(self, filename: str) -> None:
        time.sleep(1)  # wait just a bit, because Popen runs file asynchronously
        logger.debug('Deleting a temporary file %s', filename)
        os.remove(filename)
