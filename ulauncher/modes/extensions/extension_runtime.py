from __future__ import annotations

import asyncio
import logging
import signal
from collections import deque
from time import time
from typing import Callable, Literal
from weakref import WeakSet

from gi.repository import Gio, GLib

ExtensionRuntimeError = Literal["Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid"]
logger = logging.getLogger()
ErrorHandlerCallback = Callable[[ExtensionRuntimeError, str], None]
aborted_subprocesses: WeakSet[Gio.Subprocess] = WeakSet()


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
        aborted_subprocesses.add(self.subprocess)
        self.subprocess.send_signal(signal.SIGTERM)
        await asyncio.sleep(0.6)  # wait for graceful shutdown (0.5s)
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
        if self.subprocess in aborted_subprocesses:
            logger.info('Extension "%s" was stopped by the user', self.ext_id)
            return

        if self.error_handler:
            uptime_seconds = time() - self.start_time
            exit_status = self.subprocess.get_exit_status()
            error_msg = "\n".join(self.recent_errors)
            if "ModuleNotFoundError" in error_msg:
                package_name = error_msg.split("'")[1].split(".")[0]
                if package_name == "ulauncher":
                    self.error_handler("MissingInternals", error_msg)
                    return
                if package_name:
                    self.error_handler("MissingModule", package_name)
                    return
            if uptime_seconds < 1:
                logger.error('Extension "%s" terminated before it could start', self.ext_id)
                self.error_handler("Terminated", error_msg)
                return

            if not error_msg:
                error_msg = f'Extension "{self.ext_id}" exited with code {exit_status} after {uptime_seconds} seconds.'

            self.error_handler("Exited", error_msg)
