from __future__ import annotations  # noqa: N999

import json
import logging
import os
from functools import partial
from typing import Any

from gi.repository import GLib

import ulauncher.api
from ulauncher.utils.message_socket import MessageSocket
from ulauncher.utils.timer import timer

logger = logging.getLogger()


class Client:
    extension: ulauncher.api.Extension
    msg_socket: MessageSocket
    mainloop: GLib.MainLoop
    """
    Manages the extension's communication with Ulauncher.

    The socket connection is established before this process starts:
    - Ulauncher (parent process) creates a socket pair (two connected endpoints)
    - Parent keeps one endpoint, passes the other's FD to child process (this)

    Communication layers:
    → Extension subclass
    • This class
    → MessageSocket (wraps a socket file descriptor)
    → (OS) Unix socket connection
    → Ulauncher ExtensionRuntime (parent runtime)
    """

    def __init__(self, extension: ulauncher.api.Extension) -> None:
        file_descriptor = int(os.environ.get("SOCKETPAIR_FD", "0"))

        self.extension = extension
        self.mainloop = GLib.MainLoop()
        self.msg_socket = MessageSocket(file_descriptor)

    def on_io_event(self, _channel: GLib.IOChannel, condition: GLib.IOCondition) -> bool:
        """
        Socket I/O event listener.
        Returns True to keep watching, False to remove the watch.
        """
        # condition can have multiple flags set simultaneously (hence the bitwise operators)
        if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
            logger.debug("Socket closed or error occurred")
            self.unload()
            return False

        if condition & GLib.IOCondition.IN:
            line = self.msg_socket.read_msg()

            if line is None:
                logger.info("Received None data before HUP, unloading.")
                self.unload()
                return False

            if line:
                try:
                    obj = json.loads(line)
                    self.on_message(obj)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from Ulauncher app %s:", line)

        return True

    def connect(self) -> None:
        """
        Sets up I/O event monitoring and starts the GLib mainloop (blocks thread).
        """
        # Create IOChannel for event monitoring
        # Must be set to not buffer, or it would steal data from msg_socket
        io_channel = GLib.IOChannel.unix_new(self.msg_socket.file_descriptor)
        io_channel.set_encoding(None)
        io_channel.set_buffered(False)

        GLib.io_add_watch(
            io_channel, GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR, self.on_io_event
        )

        logger.debug("Starting GLib mainloop")
        self.mainloop.run()
        logger.debug("GLib mainloop stopped")

    def on_message(self, event: dict[str, Any]) -> None:
        """
        Parses message from Ulauncher and triggers extension event
        """
        logger.debug("Incoming event: %s", event)
        self.extension.trigger_event(event)

    def unload(self, status_code: int = 0) -> None:
        # extension has 0.5 sec to save it's state, after that it will be terminated
        self.extension.trigger_event({"type": "event:unload"})
        timer(0.5, partial(os._exit, status_code))
        # Quit mainloop to exit after current event, needed to unblock and for the shutdown to proceed
        if self.mainloop.is_running():
            self.mainloop.quit()

    def send(self, response: Any) -> None:
        """Send a JSON object as a message."""
        logger.debug('Send message with keys "%s"', set(response))
        json_str = json.dumps(response)
        self.msg_socket.write_msg(json_str)
