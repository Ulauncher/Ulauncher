import logging
import os
import shlex
import subprocess
import tempfile
import time

from ulauncher.utils.decorator.run_async import run_async

logger = logging.getLogger()


@run_async  # must be async because the script may be launching blocking processes like pkexec (issue 1299)
def run_script(script: str, arg: str) -> None:
    file_path = f"{tempfile.gettempdir()}/ulauncher_run_script_{time.time()}"
    with open(file_path, "w") as file:
        file.write(script)
    try:
        os.chmod(file_path, 0o700)
        logger.debug("Running a script from %s", file_path)
        output = subprocess.check_output([file_path + " " + shlex.quote(arg)], shell=True).decode("utf-8")
        logger.debug("Script action output:\n%s", output)
    finally:
        logger.debug("Deleting a temporary file %s", file_path)
        os.remove(file_path)
