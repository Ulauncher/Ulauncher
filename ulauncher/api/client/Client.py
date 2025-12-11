from __future__ import annotations  # noqa: N999

import logging
import os
from typing import Any

from gi.repository import GLib

import ulauncher.api
from ulauncher.utils.socket_msg_controller import SocketMsgController

logger = logging.getLogger()


class Client:
    extension: ulauncher.api.Extension
    msg_controller: SocketMsgController
    mainloop: GLib.MainLoop
    """
    Manages the extension's communication with Ulauncher.

    The socket connection is established before this process starts:
    - Ulauncher (parent process) creates a socket pair (two connected endpoints)
    - Parent keeps one endpoint, passes the other's FD to child process (this)

    Communication layers:
    → Extension subclass
    • This class
    → SocketMsgController
    → (OS) Unix socket (pair) connection
    → Ulauncher ExtensionRuntime (parent runtime)
    """

    def __init__(self, extension: ulauncher.api.Extension) -> None:
        fd_str = os.environ.get("SOCKETPAIR_FD")
        if not fd_str:
            err_msg = "SOCKETPAIR_FD environment variable is required"
            raise RuntimeError(err_msg)
        try:
            file_descriptor = int(fd_str)
        except (TypeError, ValueError) as exc:
            err_msg = "SOCKETPAIR_FD must be a valid integer"
            raise RuntimeError(err_msg) from exc

        self.extension = extension
        self.mainloop = GLib.MainLoop()
        self.msg_controller = SocketMsgController(file_descriptor, on_close=self.unload)

    def connect(self) -> None:
        """
        Sets up message listener and starts the GLib mainloop (blocks thread).
        """
        self.msg_controller.listen(self.on_message)

        logger.debug("Starting GLib mainloop")
        self.mainloop.run()
        logger.debug("GLib mainloop stopped")

    def on_message(self, event: dict[str, Any]) -> None:
        """
        Parses message from Ulauncher and triggers extension event
        """
        logger.debug("Incoming event: %s", event)
        self.extension.trigger_event(event)

    def unload(self) -> None:
        # trigger unload event and release mainloop so that the process will exit after the event is handled
        self.extension.trigger_event({"type": "event:unload"})
        if self.mainloop.is_running():
            self.mainloop.quit()

    def send(self, response: dict[str, Any]) -> None:
        """Send a JSON object as a message."""
        logger.debug('Send message with keys "%s"', set(response))
        self.msg_controller.send(response)
