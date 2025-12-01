from __future__ import annotations

import logging
import signal
from collections import deque
from time import time
from typing import Callable, Literal
from weakref import WeakSet

from gi.repository import Gio, GLib

from ulauncher.utils.timer import timer

ExtensionExitCause = Literal[
    "Stopped", "Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid"
]
logger = logging.getLogger()
ExitHandlerCallback = Callable[[ExtensionExitCause, str], None]
aborted_subprocesses: WeakSet[Gio.Subprocess] = WeakSet()


class ExtensionRuntime:
    ext_id: str
    subprocess: Gio.Subprocess
    start_time: float
    error_stream: Gio.DataInputStream
    recent_errors: deque[str]
    exit_handler: ExitHandlerCallback | None

    def __init__(
        self,
        ext_id: str,
        cmd: list[str],
        env: dict[str, str] | None = None,
        exit_handler: ExitHandlerCallback | None = None,
    ) -> None:
        self.ext_id = ext_id
        self.exit_handler = exit_handler
        self.recent_errors = deque(maxlen=1)
        self.start_time = time()
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)
        for env_name, env_value in (env or {}).items():
            launcher.setenv(env_name, env_value, True)
        launcher.setenv("ULAUNCHER_EXTENSION_ID", ext_id, True)

        self.subprocess = launcher.spawnv(cmd)
        error_input_stream = self.subprocess.get_stderr_pipe()
        if not error_input_stream:
            err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDERR_PIPE"
            raise AssertionError(err_msg)
        self.error_stream = Gio.DataInputStream.new(error_input_stream)

        logger.debug("Launched %s using Gio.Subprocess", self.ext_id)
        self.subprocess.wait_async(None, self.handle_exit)
        self.read_stderr_line()

    def stop(self) -> None:
        """
        Terminates extension
        """
        if not self.subprocess.get_identifier():
            logger.info("Cannot stop '%s'. It has already been terminated, or was never started", self.ext_id)
            return

        logger.info('Terminating extension "%s"', self.ext_id)
        aborted_subprocesses.add(self.subprocess)
        self.subprocess.send_signal(signal.SIGTERM)
        # wait for graceful shutdown before forcibly killing (client needs 0.5s so padding 25ms extra)
        timer(0.525, self._kill)

    def _kill(self) -> None:
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
            print(output, f" 🔌 from {self.ext_id}")  # noqa: T201
            self.recent_errors.append(output)
            self.read_stderr_line()

    def handle_exit(self, _subprocess: Gio.Subprocess, _result: Gio.AsyncResult) -> None:
        if self.subprocess in aborted_subprocesses:
            if self.exit_handler:
                self.exit_handler("Stopped", "Extension was stopped by the user")
            logger.info('Extension "%s" was stopped by the user', self.ext_id)
            return

        if self.exit_handler:
            uptime_seconds = time() - self.start_time
            exit_status = self.subprocess.get_exit_status()
            error_msg = "\n".join(self.recent_errors)
            if "ModuleNotFoundError" in error_msg:
                package_name = error_msg.split("'")[1].split(".")[0]
                if package_name == "ulauncher":
                    self.exit_handler("MissingInternals", error_msg)
                    return
                if package_name:
                    self.exit_handler("MissingModule", package_name)
                    return
            if uptime_seconds < 1:
                logger.error('Extension "%s" terminated before it could start', self.ext_id)
                self.exit_handler("Terminated", error_msg)
                return

            if not error_msg:
                error_msg = f'Extension "{self.ext_id}" exited with code {exit_status} after {uptime_seconds} seconds.'

            self.exit_handler("Exited", error_msg)
