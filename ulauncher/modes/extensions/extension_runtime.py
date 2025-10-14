from __future__ import annotations

import asyncio
import json
import logging
import signal
from collections import deque
from time import time
from typing import Any, Callable, Literal
from weakref import WeakSet

from gi.repository import Gio, GLib

from ulauncher.utils.eventbus import EventBus

ExtensionRuntimeError = Literal["Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid"]
logger = logging.getLogger()
events = EventBus()
ExitHandlerCallback = Callable[[ExtensionRuntimeError, str], None]
aborted_subprocesses: WeakSet[Gio.Subprocess] = WeakSet()


class ExtensionRuntime:
    ext_id: str
    subprocess: Gio.Subprocess
    start_time: float
    stdin: Gio.DataOutputStream
    stderr: Gio.DataInputStream
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

        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDIN_PIPE | Gio.SubprocessFlags.STDERR_PIPE)

        for env_name, env_value in (env or {}).items():
            launcher.setenv(env_name, env_value, True)

        self.subprocess = launcher.spawnv(cmd)

        if stdin_base_stream := self.subprocess.get_stdin_pipe():
            self.stdin = Gio.DataOutputStream.new(stdin_base_stream)

        if stderr_base_stream := self.subprocess.get_stderr_pipe():
            self.stderr = Gio.DataInputStream.new(stderr_base_stream)

        logger.debug("Launched %s using Gio.Subprocess", self.ext_id)
        self.subprocess.wait_async(None, self.handle_exit)
        self.read_stderr_line()

    async def stop(self) -> None:
        """
        Terminates extension
        """
        if not self.subprocess.get_identifier():
            logger.info("Cannot stop '%s'. It has already been terminated, or was never started", self.ext_id)
            return

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
        self.stderr.read_line_async(GLib.PRIORITY_DEFAULT, None, self.handle_stderr)

    def send_message(self, message: dict[str, Any]) -> None:
        """Send a JSON message to extension stdin."""
        if self.stdin:
            try:
                json_str = json.dumps(message) + "\n"
                self.stdin.write(json_str.encode())
                self.stdin.flush()
                logger.debug("Sent message to %s: %s", self.ext_id, message)
            except Exception:
                logger.exception("Failed to send stdin message to %s", self.ext_id)

    def handle_stderr(self, stderr: Gio.DataInputStream, result: Gio.AsyncResult) -> None:
        # append output to recent_errors
        output, _ = stderr.read_line_finish_utf8(result)
        if output:
            try:
                message = json.loads(output)
                logger.debug('Incoming response with keys "%s" from "%s"', set(message), self.ext_id)
                events.emit("extensions:handle_response", self.ext_id, message)
            except json.JSONDecodeError:
                print(output)  # noqa: T201
                self.recent_errors.append(output)

            self.read_stderr_line()

    def handle_exit(self, _subprocess: Gio.Subprocess, _result: Gio.AsyncResult) -> None:
        if self.subprocess in aborted_subprocesses:
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
