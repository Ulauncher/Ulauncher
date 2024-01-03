from __future__ import annotations

import logging
import signal
import sys
from collections import deque
from functools import lru_cache, partial
from time import time
from typing import Callable, NamedTuple

if sys.version_info >= (3, 8):
    from typing import Literal

    ExtensionRuntimeError = Literal["Terminated", "Exited", "MissingModule", "Incompatible", "Invalid"]
else:
    ExtensionRuntimeError = str

from gi.repository import Gio, GLib

from ulauncher.utils.timer import timer

logger = logging.getLogger()


ErrorHandlerCallback = Callable[[ExtensionRuntimeError, str], None]


class ExtensionProc(NamedTuple):
    ext_id: str
    subprocess: Gio.Subprocess
    start_time: float
    error_stream: Gio.DataInputStream
    recent_errors: deque
    error_handler: ErrorHandlerCallback | None

    def extract_error(self) -> tuple[ExtensionRuntimeError, str]:
        if self.subprocess.get_if_signaled():
            kill_signal = self.subprocess.get_term_sig()
            return "Terminated", f'Extension "{self.ext_id}" was terminated with signal {kill_signal}'

        uptime_seconds = time() - self.start_time
        code = self.subprocess.get_exit_status()
        error_msg = "\n".join(self.recent_errors)
        logger.error('Extension "%s" exited with an error: %s', self.ext_id, error_msg)
        if "ModuleNotFoundError" in error_msg:
            package_name = error_msg.split("'")[1]
            if package_name == "ulauncher":
                logger.error(
                    "Extension tried to import Ulauncher modules which have been moved or removed. "
                    "This is likely Ulauncher internals which were not part of the extension API. "
                    "Extensions importing these can break at any Ulauncher release."
                )
                return "Incompatible", error_msg
            if package_name:
                return "MissingModule", package_name
        if uptime_seconds < 1:
            return "Terminated", error_msg

        error_msg = f'Extension "{self.ext_id}" exited with code {code} after {uptime_seconds} seconds.'
        return "Exited", error_msg


class ExtensionRunner:
    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls) -> ExtensionRunner:
        return cls()

    def __init__(self) -> None:
        self.extension_procs: dict[str, ExtensionProc] = {}

    def run(
        self,
        ext_id: str,
        cmd: list[str],
        env: dict[str, str] | None = None,
        error_handler: ErrorHandlerCallback | None = None,
    ) -> None:
        """
        * Validates manifest
        * Runs extension in a new process
        """
        if not self.is_running(ext_id):
            launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)
            for env_name, env_value in (env or {}).items():
                launcher.setenv(env_name, env_value, True)

            t_start = time()
            subproc = launcher.spawnv(cmd)
            error_input_stream = subproc.get_stderr_pipe()
            if not error_input_stream:
                err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDERR_PIPE"
                raise AssertionError(err_msg)
            error_line_str = Gio.DataInputStream.new(error_input_stream)
            proc = ExtensionProc(
                ext_id=ext_id,
                error_handler=error_handler,
                subprocess=subproc,
                start_time=t_start,
                error_stream=error_line_str,
                recent_errors=deque(maxlen=1),
            )
            self.extension_procs[ext_id] = proc
            logger.debug("Launched %s using Gio.Subprocess", ext_id)

            subproc.wait_async(None, self.handle_exit, ext_id)
            self.read_stderr_line(proc)

    def read_stderr_line(self, proc: ExtensionProc) -> None:
        proc.error_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.handle_stderr, proc.ext_id)

    def handle_stderr(self, error_stream: Gio.DataInputStream, result: Gio.AsyncResult, ext_id: str) -> None:
        output, _ = error_stream.read_line_finish_utf8(result)
        if output:
            print(output)  # noqa: T201
        proc = self.extension_procs.get(ext_id)
        if not proc:
            logger.debug("Extension process context for %s no longer present", ext_id)
            return
        if output:
            proc.recent_errors.append(output)
        self.read_stderr_line(proc)

    def handle_exit(self, subprocess: Gio.Subprocess, _result: Gio.AsyncResult, ext_id: str) -> None:
        proc = self.extension_procs.get(ext_id)
        if not proc or id(proc.subprocess) != id(subprocess):
            logger.info("Exited process %s for %s has already been removed.", subprocess, ext_id)
            return
        error_type, error_msg = proc.extract_error()
        logger.error(error_msg)
        self.extension_procs.pop(ext_id, None)
        if proc.error_handler:
            proc.error_handler(error_type, error_msg)

    def stop(self, ext_id: str) -> None:
        """
        Terminates extension
        """
        if self.is_running(ext_id):
            logger.info('Terminating extension "%s"', ext_id)
            proc = self.extension_procs[ext_id]
            self.extension_procs.pop(ext_id, None)

            proc.subprocess.send_signal(signal.SIGTERM)

            timer(0.5, partial(self.confirm_termination, proc))

    def confirm_termination(self, proc: ExtensionProc) -> None:
        if proc.subprocess.get_identifier():
            logger.info("Extension %s still running, sending SIGKILL", proc.ext_id)
            # It is possible that the process exited between the check above and this signal,
            # luckily the subprocess library handles the signal delivery in race-free way, so this
            # is safe to do.
            proc.subprocess.send_signal(signal.SIGKILL)

    def is_running(self, ext_id: str) -> bool:
        return ext_id in self.extension_procs
