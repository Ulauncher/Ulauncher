import time
import os
import logging
import subprocess
import shlex
import tempfile
from ulauncher.utils.decorator.run_async import run_async

logger = logging.getLogger()


@run_async(daemon=True)
def remove_temp_file(filename: str):
    time.sleep(1)  # wait just a bit, because Popen runs file asynchronously
    logger.debug("Deleting a temporary file %s", filename)
    os.remove(filename)


def run_script(script: str, arg: str):
    file_path = f"{tempfile.gettempdir()}/ulauncher_run_script_{time.time()}"
    with open(file_path, "w") as file:
        file.write(script)
    try:
        os.chmod(file_path, 0o777)
        logger.debug("Running a script from %s", file_path)
        output = subprocess.check_output([file_path + " " + shlex.quote(arg)], shell=True).decode("utf-8")
        logger.debug("Script action output:\n%s", output)
        remove_temp_file(file_path)
    except Exception:
        remove_temp_file(file_path)
        raise
