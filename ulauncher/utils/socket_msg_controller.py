from __future__ import annotations

import contextlib
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

    def _trigger_close(self) -> None:
        """
        Trigger the on_close callback if set, ensuring it's only called once.
        """
        callback = self._on_close
        self._on_close = None
        if callback:
            callback()

    def close(self) -> None:
        """
        Close the socket and cleanup resources.
        """
        # separate suppress statements so that both will try to close even if one errors
        with contextlib.suppress(GLib.Error):
            self._input_stream.close(None)
        with contextlib.suppress(GLib.Error):
            self._output_stream.close(None)
        self._trigger_close()

    def send(self, data: dict[str, Any]) -> None:
        """
        Serialize a dictionary to JSON and send it to the socket.
        """
        try:
            json_str = json.dumps(data)
        except (TypeError, ValueError, RecursionError) as e:
            logger.warning("Data not JSON serializable %s", e)
            return

        try:
            self._output_stream.put_string(json_str + "\n")
            self._output_stream.flush()
        except GLib.Error as e:
            logger.warning("Failed to send message, connection likely closed: %s", e)
            self._trigger_close()

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
                self._trigger_close()
                return

            if message_str is None:
                # Connection closed normally
                self._trigger_close()
                return

            try:
                on_message(json.loads(message_str))
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received: %s", message_str)

            # Continue reading next message
            self.listen(on_message)

        self._input_stream.read_line_async(GLib.PRIORITY_DEFAULT, None, handle_read)
