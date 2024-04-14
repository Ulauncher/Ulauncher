from __future__ import annotations

import logging
import os
import sys
import traceback
from functools import partial
from typing import Any

from gi.repository import Gio, GLib

import ulauncher.api
from ulauncher.api.shared.socket_path import get_socket_path
from ulauncher.utils.framer import JSONFramer
from ulauncher.utils.timer import timer

logger = logging.getLogger()


class Client:
    """
    Instantiated in extension code and manages data transfer from/to Ulauncher app

    :param ~ulauncher.api.Extension extension:
    """

    def __init__(self, extension: ulauncher.api.Extension) -> None:
        self.socket_path = get_socket_path()
        self.extension = extension
        self.client = Gio.SocketClient()
        self.conn = None
        self.framer = None

    def connect(self) -> None:
        """
        Connects to the extension server and blocks thread
        """
        self.conn = self.client.connect(Gio.UnixSocketAddress.new(self.socket_path), None)  # type: ignore[assignment]
        if not self.conn:
            msg = f"Failed to connect to socket_path {self.socket_path}"
            raise RuntimeError(msg)
        self.framer = JSONFramer()
        self.framer.connect("message_parsed", self.on_message)
        self.framer.connect("closed", self.on_close)
        self.framer.set_connection(self.conn)
        self.send({"type": "extension:socket_connected", "ext_id": self.extension.ext_id})

        mainloop = GLib.MainLoop.new(None, False)
        mainloop.run()

    def on_message(self, _framer: JSONFramer, event: dict[str, Any]) -> None:
        """
        Parses message from Ulauncher and triggers extension event

        :param ulauncher.utils.framer.JSONFramer framer:
        :param ulauncher.api.shared.events.Event event:
        """
        logger.debug("Incoming event %s", type(event).__name__)
        try:
            self.extension.trigger_event(event)
        except Exception:
            traceback.print_exc(file=sys.stderr)

    def on_close(self, _framer: JSONFramer) -> None:
        """
        Terminates extension process on client disconnect.

        Triggers :class:`~ulauncher.api.shared.event.UnloadEvent` for graceful shutdown

        :param ulauncher.utils.framer.JSONFramer framer:
        """
        logger.warning("Connection closed. Exiting")
        self.extension.trigger_event({"type": "event:unload"})
        # extension has 0.5 sec to save it's state, after that it will be terminated
        timer(0.5, partial(os._exit, 0))

    def send(self, response: Any) -> None:
        """
        Sends response to Ulauncher

        :param dict response:
        """
        logger.debug('Send message with keys "%s"', set(response))
        assert self.framer
        self.framer.send(response)
