from __future__ import annotations

import json
import logging
import signal
import socket
from collections import deque
from time import time
from typing import Any, Callable, Literal
from weakref import WeakSet

from gi.repository import Gio, GLib

from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.socket_msg_controller import SocketMsgController
from ulauncher.utils.timer import timer

ExtensionExitCause = Literal[
    "Stopped", "Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid"
]
ExitHandlerCallback = Callable[[ExtensionExitCause, str], None]
logger = logging.getLogger()
events = EventBus()


aborted_subprocesses: WeakSet[Gio.Subprocess] = WeakSet()


class ExtensionRuntime:
    ext_id: str
    subprocess: Gio.Subprocess
    start_time: float
    msg_socket: SocketMsgController
    parent_socket: socket.socket
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

        extension_env = env.copy() if env else {}
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)

        for env_name, env_value in extension_env.items():
            launcher.setenv(env_name, env_value, True)
        launcher.setenv("ULAUNCHER_EXTENSION_ID", ext_id, True)

        # Create both parent and child sockets. The child is only used to get the file descriptor
        # for the subprocess
        self.parent_socket, child_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        child_fd = child_socket.fileno()

        launcher.setenv("SOCKETPAIR_FD", str(child_fd), True)
        launcher.take_fd(child_fd, child_fd)

        self.subprocess = launcher.spawnv(cmd)

        # Now it's safe to close the unused child socket
        child_socket.close()

        # Socket handler for parent process
        self.msg_socket = SocketMsgController(self.parent_socket.fileno())

        error_input_stream = self.subprocess.get_stderr_pipe()
        if not error_input_stream:
            err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDERR_PIPE"
            raise AssertionError(err_msg)
        self.error_stream = Gio.DataInputStream.new(error_input_stream)

        logger.debug("Launched %s using Gio.Subprocess", self.ext_id)
        self.subprocess.wait_async(None, self.handle_exit)
        self.read_stderr_line()
        self.read_socket_message()
        events.emit("extensions:invalidate_cache")

    def stop(self) -> None:
        """
        Terminates extension
        """
        if not self.subprocess.get_identifier():
            logger.info("Cannot stop '%s'. It has already been terminated, or was never started", self.ext_id)
            return

        logger.info('Terminating extension "%s"', self.ext_id)
        aborted_subprocesses.add(self.subprocess)

        try:
            self.parent_socket.close()
        except Exception:
            logger.exception("Error closing socket for %s", self.ext_id)

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

    def send_message(self, message: dict[str, Any]) -> None:
        """Send a JSON message to extension."""
        try:
            json_str = json.dumps(message)
            self.msg_socket.write_msg(json_str)
            logger.debug("Sent message to %s: %s", self.ext_id, message)
        except Exception:
            logger.exception("Failed to send message to %s", self.ext_id)

    def read_socket_message(self) -> None:
        """Start reading messages from asynchronously."""
        self.msg_socket.input_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.handle_socket_message)

    def handle_socket_message(self, input_stream: Gio.DataInputStream, result: Gio.AsyncResult) -> None:
        """Handle incoming message from socket pair."""
        try:
            message_str, _ = input_stream.read_line_finish_utf8(result)
            if message_str:
                try:
                    message = json.loads(message_str)
                    logger.debug('Incoming response with keys "%s" from "%s"', set(message), self.ext_id)
                    events.emit("extensions:handle_response", self.ext_id, message)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from extension %s: %s", self.ext_id, message_str)
                # Continue reading
                self.read_socket_message()
        except Exception:
            logger.exception("Error reading message from %s", self.ext_id)

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

        elif self.exit_handler:
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

        events.emit("extensions:invalidate_cache")
