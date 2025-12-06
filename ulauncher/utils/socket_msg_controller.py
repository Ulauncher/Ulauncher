from __future__ import annotations

from ulauncher.utils.gio_compat import Gio


class SocketMsgController:
    """
    Takes a file descriptor from a socket pair to provides read and write methods
    """

    file_descriptor: int

    def __init__(self, file_descriptor: int) -> None:
        self.file_descriptor = file_descriptor
        unix_in_stream = Gio.UnixInputStream.new(file_descriptor, True)
        unix_out_stream = Gio.UnixOutputStream.new(file_descriptor, False)
        self.input_stream = Gio.DataInputStream.new(unix_in_stream)
        self.output_stream = Gio.DataOutputStream.new(unix_out_stream)

    def read(self) -> str | None:
        """
        Read line-delimited message from the socket.
        """
        result = self.input_stream.read_line_utf8()
        return result[0] if result else None

    def write(self, msg: str) -> None:
        """
        Write a line-delimited message to the socket (newline will be added automatically).
        """
        self.output_stream.put_string(msg + "\n")
        self.output_stream.flush()
