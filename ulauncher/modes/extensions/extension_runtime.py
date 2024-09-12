from __future__ import annotations

import asyncio
import logging
import signal
import sys
from collections import deque
from time import time
from typing import Callable

if sys.version_info >= (3, 8):
    from typing import Literal

    ExtensionRuntimeError = Literal[
        "Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid"
    ]
else:
    ExtensionRuntimeError = str

from gi.repository import Gio, GLib

logger = logging.getLogger()
ErrorHandlerCallback = Callable[[ExtensionRuntimeError, str], None]


class ExtensionRuntime:
    ext_id: str
    subprocess: Gio.Subprocess
    start_time: float
    error_stream: Gio.DataInputStream
    recent_errors: deque[str]
    error_handler: ErrorHandlerCallback | None

    def __init__(
        self,
        ext_id: str,
        cmd: list[str],
        env: dict[str, str] | None = None,
        error_handler: ErrorHandlerCallback | None = None,
    ) -> None:
        self.ext_id = ext_id
        self.error_handler = error_handler
        self.recent_errors = deque(maxlen=1)
        self.start_time = time()
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)
        for env_name, env_value in (env or {}).items():
            launcher.setenv(env_name, env_value, True)

        self.subprocess = launcher.spawnv(cmd)
        error_input_stream = self.subprocess.get_stderr_pipe()
        if not error_input_stream:
            err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDERR_PIPE"
            raise AssertionError(err_msg)
        self.error_stream = Gio.DataInputStream.new(error_input_stream)

        logger.debug("Launched %s using Gio.Subprocess", self.ext_id)
        self.subprocess.wait_async(None, self.handle_exit)
        self.read_stderr_line()

    async def stop(self) -> None:
        """
        Terminates extension
        """
        logger.info('Terminating extension "%s"', self.ext_id)
        self.subprocess.send_signal(signal.SIGTERM)
        await asyncio.sleep(0.5)
        if self.subprocess.get_identifier():
            logger.info("Extension %s still running, sending SIGKILL", self.ext_id)
            # It is possible that the process exited between the check above and this signal,
            # luckily the subprocess library handles the signal delivery in race-free way, so this
            # is safe to do.
            self.subprocess.send_signal(signal.SIGKILL)

    def read_stderr_line(self) -> None:
        self.error_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.handle_stderr)

    def handle_stderr(self, error_stream: Gio.DataInputStream, result: Gio.AsyncResult) -> None:
        # append output to recent_errors
        output, _ = error_stream.read_line_finish_utf8(result)
        if output:
            print(output)  # noqa: T201
            self.recent_errors.append(output)
            self.read_stderr_line()

    def handle_exit(self, _subprocess: Gio.Subprocess, _result: Gio.AsyncResult) -> None:
        error_type, error_msg = self.extract_error()
        logger.error(error_msg)
        if self.error_handler:
            self.error_handler(error_type, error_msg)

    def extract_error(self) -> tuple[ExtensionRuntimeError, str]:
        if self.subprocess.get_if_signaled():
            kill_signal = self.subprocess.get_term_sig()
            return "Terminated", f'Extension "{self.ext_id}" was terminated with signal {kill_signal}'

        uptime_seconds = time() - self.start_time
        code = self.subprocess.get_exit_status()
        error_msg = "\n".join(self.recent_errors)
        logger.error('Extension "%s" exited with an error: %s', self.ext_id, error_msg)
        if "ModuleNotFoundError" in error_msg:
            package_name = error_msg.split("'")[1].split(".")[0]
            if package_name == "ulauncher":
                return "MissingInternals", error_msg
            if package_name:
                return "MissingModule", package_name
        if uptime_seconds < 1:
            return "Terminated", error_msg

        error_msg = f'Extension "{self.ext_id}" exited with code {code} after {uptime_seconds} seconds.'
        return "Exited", error_msg
