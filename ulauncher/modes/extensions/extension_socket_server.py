from __future__ import annotations

import logging
import os
from typing import Any, Callable

from gi.repository import Gio, GObject

from ulauncher.internals.query import Query
from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.framer import JSONFramer
from ulauncher.utils.socket_path import get_socket_path

logger = logging.getLogger()

# This event bus is used to communicate between the ExtensionSocketServer class and the rest of the app
# Communication further down to the extension level is done through Gio.SocketService and Unix sockets
events = EventBus()


class ExtensionSocketServer:
    socket_path: str
    service: Gio.SocketService | None
    socket_controllers: dict[str, ExtensionSocketController]
    pending: dict[int, tuple[JSONFramer, int, int]]
    active_socket_controller: ExtensionSocketController | None = None
    on_extension_registered_callback: Callable[[str], None]

    def __init__(self, on_extension_registered_callback: Callable[[str], None]) -> None:
        self.service = None
        self.socket_path = get_socket_path()
        self.socket_controllers = {}
        self.pending = {}
        self.on_extension_registered_callback = on_extension_registered_callback
        events.set_self(self)

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
        self.socket_controllers = {}

    def handle_query(self, ext_id: str, query: Query) -> bool:
        """
        Handles the query.
        :returns: True if it found an active socket controller for the given ext_id
        """
        if not query.keyword:
            logger.warning("Extensions currently only support queries with a keyword: %s", query)
            return False

        if socket_controller := self.socket_controllers.get(ext_id):
            self.active_socket_controller = socket_controller
            socket_controller.handle_query(query)
            return True

        return False

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
            if pended := self.pending.pop(id(framer)):
                for msg_id in pended[1:]:
                    GObject.signal_handler_disconnect(framer, msg_id)
            ext_id: str | None = event.get("ext_id")
            assert ext_id
            ExtensionSocketController(self.socket_controllers, framer, ext_id)
            self.on_extension_registered_callback(ext_id)
        else:
            logger.debug("Unhandled message received: %s", event)

    def stop(self) -> None:
        if self.service:
            self.service.stop()
            self.service.close()
            self.service = None

    def trigger_event(self, event: dict[str, Any]) -> None:
        ext_id = event.get("ext_id")
        socket_controller = self.socket_controllers.get(ext_id) if ext_id else self.active_socket_controller
        if socket_controller:
            socket_controller.trigger_event(event)
            self.active_socket_controller = socket_controller

    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        if socket_controller := self.socket_controllers.get(ext_id):
            for p_id, new_value in data.get("preferences", {}).items():
                pref = socket_controller.ext_controller.preferences.get(p_id)
                if pref and new_value != pref.value:
                    event_data = {"type": "event:update_preferences", "args": [p_id, new_value, pref.value]}
                    socket_controller.send_message(event_data)

    def handle_response(self, ext_id: str, response: dict[str, Any]) -> None:
        socket_controller = self.socket_controllers.get(ext_id)
        if not self.active_socket_controller:
            self.active_socket_controller = socket_controller
        elif self.active_socket_controller != socket_controller:
            # This can happen if the extension was killed from a task manager
            logger.warning("Received response from different controller or event")
            return

        events.emit("extensions:handle_action", response.get("action"))
