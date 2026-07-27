from __future__ import annotations

import logging
import signal
import socket
from collections import deque
from time import time
from typing import Callable, Literal, cast
from weakref import WeakSet

from ulauncher.gi import Gio, GLib
from ulauncher.internals import ipc, log_wire
from ulauncher.utils import scheduling
from ulauncher.utils.socket_msg_controller import SocketMsgController

DEBUGPY_HOST = "127.0.0.1"
DEBUGPY_PORT = 5678

ExtensionExitCause = Literal[
    "Stopped", "Terminated", "Exited", "MissingModule", "MissingInternals", "Incompatible", "Invalid", "FailedToStart"
]
ExitHandlerCallback = Callable[[ExtensionExitCause, str], None]
MessageHandlerCallback = Callable[[ipc.ExtensionMessage], None]
logger = logging.getLogger(__name__)


aborted_subprocesses: WeakSet[Gio.Subprocess] = WeakSet()


class ExtensionRuntime:
    _ext_id: str
    _subprocess: Gio.Subprocess
    _start_time: float
    _msg_controller: SocketMsgController
    _parent_socket: socket.socket | None = None
    _output_streams: dict[str, Gio.DataInputStream]
    _recent_errors: deque[str]
    _exit_handler: ExitHandlerCallback | None
    _message_handler: MessageHandlerCallback | None

    def __init__(
        self,
        ext_id: str,
        cmd: list[str],
        env: dict[str, str] | None = None,
        exit_handler: ExitHandlerCallback | None = None,
        message_handler: MessageHandlerCallback | None = None,
    ) -> None:
        self._ext_id = ext_id
        self._exit_handler = exit_handler
        self._message_handler = message_handler
        self._recent_errors = deque(maxlen=1)
        self._start_time = time()

        extension_env: dict[str, str] = env.copy() if env else {}
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE)

        for env_name, env_value in extension_env.items():
            launcher.setenv(env_name, env_value, True)
        launcher.setenv("ULAUNCHER_EXTENSION_ID", ext_id, True)
        # Python block-buffers stdout when it isn't a terminal, holding back `print` output
        launcher.setenv("PYTHONUNBUFFERED", "1", True)

        def socket_cleanup() -> None:
            if self._parent_socket:
                self._parent_socket.close()
                self._parent_socket = None
                logger.info("Extension %s connection closed", self._ext_id)

        try:
            # Create both parent and child sockets. The child fd is detached and handed over to the launcher.
            # The parent needs to be stored as a property to avoid getting garbage collected prematurely.
            self._parent_socket, child_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
            child_fd = child_socket.detach()

            launcher.setenv("SOCKETPAIR_FD", str(child_fd), True)
            launcher.take_fd(child_fd, child_fd)

            self._subprocess = launcher.spawnv(cmd)

            # Socket handler for parent process
            self._msg_controller = SocketMsgController(self._parent_socket.fileno(), socket_cleanup)
        except (OSError, GLib.Error, TypeError):
            socket_cleanup()
            raise

        out_pipe = self._subprocess.get_stdout_pipe()
        err_pipe = self._subprocess.get_stderr_pipe()
        if not out_pipe or not err_pipe:
            err_msg = "Subprocess must be created with Gio.SubprocessFlags.STDOUT_PIPE and STDERR_PIPE"
            raise AssertionError(err_msg)
        self._output_streams = {
            "stdout": Gio.DataInputStream.new(out_pipe),
            "stderr": Gio.DataInputStream.new(err_pipe),
        }

        logger.debug("Launched %s using Gio.Subprocess", self._ext_id)
        self._subprocess.wait_async(None, self.handle_exit)
        for name in self._output_streams:
            self.read_output_line(name)
        self._msg_controller.listen(self.handle_message)

    def stop(self) -> None:
        """
        Terminates extension
        """
        if not self._subprocess.get_identifier():
            logger.info("Cannot stop '%s'. It has already been terminated, or was never started", self._ext_id)
            return

        logger.info('Terminating extension "%s"', self._ext_id)
        aborted_subprocesses.add(self._subprocess)

        self._msg_controller.close()
        # wait for graceful shutdown before forcibly killing
        scheduling.timer(0.5, self._kill)

    def _kill(self) -> None:
        if self._subprocess.get_identifier():
            logger.info("Sending SIGKILL to extension %s", self._ext_id)
            # The process may exit between this check and the signal; Gio delivers it race-free.
            self._subprocess.send_signal(signal.SIGKILL)

    def read_output_line(self, stream_name: str) -> None:
        stream = self._output_streams[stream_name]
        stream.read_line_async(
            GLib.PRIORITY_DEFAULT, None, lambda source, result: self.handle_output(source, result, stream_name)
        )

    def send_message(self, message: ipc.Event, request_id: int | None = None) -> None:
        self._msg_controller.send([message, request_id])
        logger.debug("Sent message to %s: %s (request_id=%s)", self._ext_id, message, request_id)

    def handle_message(self, message: object) -> None:
        # message is a ipc.ExtensionMessage that has gone through the IPC json layer,
        # converting Results to dicts. ExtensionMode.handle_message rehydrates it
        if not isinstance(message, dict) or "name" not in message:
            logger.warning("Extension %s sent invalid message format: %s", self._ext_id, message)
            return
        if self._message_handler:
            self._message_handler(cast("ipc.ExtensionMessage", message))

    def handle_output(self, stream: Gio.DataInputStream, result: Gio.AsyncResult, stream_name: str) -> None:
        try:
            output, _ = stream.read_line_finish_utf8(result)
        except GLib.Error as error:
            # A decode error only fails its own line, so keep reading. Any other error means the
            # stream is broken, and re-reading it would fail the same way.
            if error.matches(GLib.convert_error_quark(), GLib.ConvertError.ILLEGAL_SEQUENCE):
                logger.warning("Skipping undecodable %s line for %s", stream_name, self._ext_id)
                self.read_output_line(stream_name)
                return
            logger.exception("Failed to read %s line for %s", stream_name, self._ext_id)
            return

        # Only None ends the stream. A blank line reads as "" and must keep the loop going, but
        # isn't emitted - _recent_errors holds one line, which a blank would evict.
        if output is None:
            return

        if output:
            message = self.emit_output(output, stream_name)
            if message and stream_name == "stderr":
                self._recent_errors.append(message)
        self.read_output_line(stream_name)

    def emit_output(self, output: str, stream_name: str) -> str:
        """Re-emit what the extension wrote through Ulauncher's handlers. Returns the message."""
        record = log_wire.parse(output, self._ext_id)
        if not record:
            # Unformatted stderr is a traceback or warning, and has to clear the app's WARNING level
            level = logging.WARNING if stream_name == "stderr" else logging.INFO
            record = logging.LogRecord(self._ext_id, level, "", 0, output, None, None, func=stream_name)
        logging.getLogger(record.name).handle(record)
        return record.getMessage()

    def handle_exit(self, _subprocess: Gio.Subprocess, _result: Gio.AsyncResult) -> None:
        self._msg_controller.close()

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
