import logging
import os
import shlex
import subprocess
import tempfile

from ulauncher.utils.decorator.run_async import run_async

logger = logging.getLogger()


@run_async  # must be async because the script may be launching blocking processes like pkexec (issue 1299)
def run_script(script: str, arg: str) -> None:
    file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", prefix="ulauncher_run_script_", delete=False) as tmp:
            file_path = tmp.name
            os.fchmod(tmp.fileno(), 0o700)
            tmp.write(script)
        logger.debug("Running a script from %s", file_path)
        # shell=True lets shebang-less scripts work: if exec(2) returns ENOEXEC the
        # shell falls back to interpreting the file as a shell script.
        output = subprocess.check_output(file_path + " " + shlex.quote(arg), shell=True).decode("utf-8")
        logger.debug("Script output:\n%s", output)
    finally:
        if file_path:
            logger.debug("Deleting a temporary file %s", file_path)
            os.remove(file_path)
