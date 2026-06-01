import logging
import os
import shlex
import subprocess
import tempfile

from ulauncher.utils.subprocess_utils import run_command

logger = logging.getLogger(__name__)


def run_script(script: str, arg: str) -> None:
    # Runs via Gio.Subprocess (not a blocking call) because the script may launch long-running or
    # blocking processes like pkexec (issue 1299). The temp file is deleted once the process exits.
    with tempfile.NamedTemporaryFile(mode="w", prefix="ulauncher_run_script_", delete=False) as tmp:
        file_path = tmp.name
        os.fchmod(tmp.fileno(), 0o700)
        tmp.write(script)
    logger.debug("Running a script from %s", file_path)

    def cleanup() -> None:
        logger.debug("Deleting a temporary file %s", file_path)
        os.remove(file_path)

    def on_success(output: str) -> None:
        logger.debug("Script output:\n%s", output)
        cleanup()

    def on_error(error: Exception) -> None:
        if isinstance(error, subprocess.CalledProcessError):
            # stderr/output are already text (the helper uses communicate_utf8); prefer stderr.
            output = (error.stderr or error.output or "").strip()
            logger.warning("Script %s exited with non-zero return code %s:\n%s", file_path, error.returncode, output)
        else:
            logger.warning("Failed to run script %s: %s", file_path, error)
        cleanup()

    # `sh -c` invokes the temp file directly. If the kernel returns ENOEXEC (shebang-less script or
    # unrecognised format), the shell falls back to interpreting it as a shell script. This is the
    # same fallback the old subprocess `shell=True` call relied on.
    command = f"{shlex.quote(file_path)} {shlex.quote(arg)}"
    run_command(["/bin/sh", "-c", command], on_success, on_error)
