from __future__ import annotations

import logging
import os
import time
from typing import Any

from gi.repository import Gio, GObject

from ulauncher.api.shared.socket_path import get_socket_path
from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.modes.extensions.ExtensionSocketController import ExtensionSocketController
from ulauncher.utils.framer import JSONFramer
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()


class ExtensionSocketServer(metaclass=Singleton):
    socket_path: str
    service: Gio.SocketService | None
    controllers: dict[str, ExtensionSocketController]
    pending: dict[int, tuple[JSONFramer, int, int]]

    def __init__(self) -> None:
        self.service = None
        self.socket_path = get_socket_path()
        self.controllers = {}
        self.pending = {}

    def start(self) -> None:
        self.service = Gio.SocketService.new()
        self.service.connect("incoming", self.handle_incoming)

        if os.path.exists(self.socket_path):
            logger.debug("Removing existing socket path %s", self.socket_path)
            os.unlink(self.socket_path)

        self.service.add_address(
            Gio.UnixSocketAddress.new(self.socket_path), Gio.SocketType.STREAM, Gio.SocketProtocol.DEFAULT, None
        )
        self.pending = {}
        self.controllers = {}
        time.sleep(0.01)
        for controller in ExtensionController.iterate():
            if controller.is_enabled and not controller.has_error:
                controller.start()

    def handle_incoming(self, _service: Any, conn: Gio.SocketConnection, _source: Any) -> None:
        framer = JSONFramer()
        msg_handler_id = framer.connect("message_parsed", self.handle_registration)
        closed_handler_id = framer.connect("closed", self.handle_pending_close)
        self.pending[id(framer)] = (framer, msg_handler_id, closed_handler_id)
        framer.set_connection(conn)

    def handle_pending_close(self, framer: JSONFramer) -> None:
        self.pending.pop(id(framer))

    def handle_registration(self, framer: JSONFramer, event: dict[str, Any]) -> None:
        if isinstance(event, dict) and event.get("type") == "extension:socket_connected":
            pended = self.pending.pop(id(framer))
            if pended:
                for msg_id in pended[1:]:
                    GObject.signal_handler_disconnect(framer, msg_id)
            ext_id: str | None = event.get("ext_id")
            assert ext_id
            ExtensionSocketController(self.controllers, framer, ext_id)
        else:
            logger.debug("Unhandled message received: %s", event)

    def stop(self) -> None:
        """
        Stops extension server
        """
        if self.service:
            self.service.stop()
            self.service.close()
            self.service = None

    def is_running(self) -> bool:
        """
        :rtype: bool
        """
        return bool(self.service)

    def get_controllers(self) -> list[ExtensionSocketController]:
        return list(self.controllers.values())

    def get_controller_by_id(self, ext_id: str) -> ExtensionSocketController | None:
        return self.controllers.get(ext_id)

    def get_controller_by_keyword(self, keyword: str) -> ExtensionSocketController | None:
        for controller in self.controllers.values():
            for trigger in controller.data_controller.user_triggers.values():
                if keyword and keyword == trigger.user_keyword:
                    return controller

        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    server = ExtensionSocketServer()
    server.start()
