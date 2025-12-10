from __future__ import annotations

import json
import logging
from typing import Any, Callable

from gi.repository import GLib

from ulauncher.utils.gio_compat import Gio

logger = logging.getLogger()


class SocketMsgController:
    """
    Takes a file descriptor from a socket pair and provides read and write methods for JSON messages.
    """

    file_descriptor: int
    _on_close: Callable[[], None] | None

    def __init__(self, file_descriptor: int, on_close: Callable[[], None] | None = None) -> None:
        self.file_descriptor = file_descriptor
        self._on_close = on_close
        unix_in_stream = Gio.UnixInputStream.new(file_descriptor, True)
        unix_out_stream = Gio.UnixOutputStream.new(file_descriptor, False)
        self._input_stream = Gio.DataInputStream.new(unix_in_stream)
        self._output_stream = Gio.DataOutputStream.new(unix_out_stream)

    def send(self, data: dict[str, Any]) -> None:
        """
        Serialize a dictionary to JSON and write it to the socket.
        """
        json_str = json.dumps(data)
        self._output_stream.put_string(json_str + "\n")
        self._output_stream.flush()

    def listen(self, on_message: Callable[[dict[str, Any]], None]) -> None:
        """
        Listen to and deserialize JSON messages from the socket.

        Args:
            on_message: Called with each successfully parsed message

        Invalid JSON messages are logged and skipped (should not happen if both sides use this class).
        Automatically continues reading until the connection is closed.
        """

        def handle_read(input_stream: Gio.DataInputStream, result: Gio.AsyncResult) -> None:
            try:
                message_str, _ = input_stream.read_line_finish_utf8(result)
            except GLib.Error:
                # I/O error - connection is broken
                if self._on_close:
                    self._on_close()
                return

            if message_str is None:
                # Connection closed normally
                if self._on_close:
                    self._on_close()
                return

            try:
                on_message(json.loads(message_str))
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received: %s", message_str)

            # Continue reading next message
            self.listen(on_message)

        self._input_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, handle_read)
