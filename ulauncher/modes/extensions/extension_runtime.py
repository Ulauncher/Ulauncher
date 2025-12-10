from __future__ import annotations

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
    _ext_id: str
    _subprocess: Gio.Subprocess
    _start_time: float
    _msg_controller: SocketMsgController
    _parent_socket: socket.socket | None = None
    _error_stream: Gio.DataInputStream
    _recent_errors: deque[str]
    _exit_handler: ExitHandlerCallback | None

    def __init__(
        self,
        ext_id: str,
        cmd: list[str],
        env: dict[str, str] | None = None,
        exit_handler: ExitHandlerCallback | None = None,
    ) -> None:
        self._ext_id = ext_id
        self._exit_handler = exit_handler
        self._recent_errors = deque(maxlen=1)
        self._start_time = time()

        extension_env = env.copy() if env else {}
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDERR_PIPE)

        for env_name, env_value in extension_env.items():
            launcher.setenv(env_name, env_value, True)
        launcher.setenv("ULAUNCHER_EXTENSION_ID", ext_id, True)

        # Create both parent and child sockets. The child fd is detached and handed over to the launcher.
        # The parent needs to be stored as a property to avoid getting garbage collected prematurely.
        self._parent_socket, child_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        child_fd = child_socket.detach()

        launcher.setenv("SOCKETPAIR_FD", str(child_fd), True)
        launcher.take_fd(child_fd, child_fd)

        self._subprocess = launcher.spawnv(cmd)

        def on_close() -> None:
            if self._parent_socket:
                self._parent_socket.close()
                self._parent_socket = None
                logger.info("Extension %s connection closed", self._ext_id)

        # Socket handler for parent process
        self._msg_controller = SocketMsgController(self._parent_socket.fileno(), on_close)

        error_input_stream = self._subprocess.get_stderr_pipe()
        if not error_input_stream:
            err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDERR_PIPE"
            raise AssertionError(err_msg)
        self._error_stream = Gio.DataInputStream.new(error_input_stream)

        logger.debug("Launched %s using Gio.Subprocess", self._ext_id)
        self._subprocess.wait_async(None, self.handle_exit)
        self.read_stderr_line()
        self._msg_controller.listen(self.handle_message)
        events.emit("extensions:invalidate_cache")

    def stop(self) -> None:
        """
        Terminates extension
        """
        if not self._subprocess.get_identifier():
            logger.info("Cannot stop '%s'. It has already been terminated, or was never started", self._ext_id)
            return

        logger.info('Terminating extension "%s"', self._ext_id)
        aborted_subprocesses.add(self._subprocess)

        try:
            if self._parent_socket:
                self._parent_socket.close()
        except Exception:
            logger.exception("Error closing socket for %s", self._ext_id)

        self._subprocess.send_signal(signal.SIGTERM)
        # wait for graceful shutdown before forcibly killing (client needs 0.5s so padding 25ms extra)
        timer(0.525, self._kill)

    def _kill(self) -> None:
        if self._subprocess.get_identifier():
            logger.info("Extension %s still running, sending SIGKILL", self._ext_id)
            # It is possible that the process exited between the check above and this signal,
            # luckily the subprocess library handles the signal delivery in race-free way, so this
            # is safe to do.
            self._subprocess.send_signal(signal.SIGKILL)

    def read_stderr_line(self) -> None:
        self._error_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.handle_stderr)

    def send_message(self, message: dict[str, Any]) -> None:
        self._msg_controller.send(message)
        logger.debug("Sent message to %s: %s", self._ext_id, message)

    def handle_message(self, message: dict[str, Any]) -> None:
        logger.debug('Incoming response with keys "%s" from "%s"', set(message), self._ext_id)
        events.emit("extensions:handle_response", self._ext_id, message)

    def handle_stderr(self, error_stream: Gio.DataInputStream, result: Gio.AsyncResult) -> None:
        # append output to recent_errors
        output, _ = error_stream.read_line_finish_utf8(result)
        if output:
            print(output, f" 🔌 from {self._ext_id}")  # noqa: T201
            self._recent_errors.append(output)
            self.read_stderr_line()

    def handle_exit(self, _subprocess: Gio.Subprocess, _result: Gio.AsyncResult) -> None:
        if self._subprocess in aborted_subprocesses:
            if self._exit_handler:
                self._exit_handler("Stopped", "Extension was stopped by the user")
            logger.info('Extension "%s" was stopped by the user', self._ext_id)

        elif self._exit_handler:
            uptime_seconds = time() - self._start_time
            exit_status = self._subprocess.get_exit_status()
            error_msg = "\n".join(self._recent_errors)
            if "ModuleNotFoundError" in error_msg:
                package_name = error_msg.split("'")[1].split(".")[0]
                if package_name == "ulauncher":
                    self._exit_handler("MissingInternals", error_msg)
                    return
                if package_name:
                    self._exit_handler("MissingModule", package_name)
                    return
            if uptime_seconds < 1:
                logger.error('Extension "%s" terminated before it could start', self._ext_id)
                self._exit_handler("Terminated", error_msg)
                return

            if not error_msg:
                error_msg = f'Extension "{self._ext_id}" exited with code {exit_status} after {uptime_seconds} seconds.'

            self._exit_handler("Exited", error_msg)

        events.emit("extensions:invalidate_cache")
