from __future__ import annotations

import logging
import os
from typing import Any

from gi.repository import Gio, GLib, GObject

from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.framer import JSONFramer
from ulauncher.utils.singleton import Singleton
from ulauncher.utils.socket_path import get_socket_path
from ulauncher.utils.timer import TimerContext, timer

LOADING_DELAY = 0.3  # delay in sec before Loading... is rendered
logger = logging.getLogger()

# This event bus is used to communicate between the ExtensionSocketServer class and the rest of the app
# Communication further down to the extension level is done through Gio.SocketService and Unix sockets
events = EventBus("extension")


class ExtensionSocketServer(metaclass=Singleton):
    socket_path: str
    service: Gio.SocketService | None
    controllers: dict[str, ExtensionSocketController]
    pending: dict[int, tuple[JSONFramer, int, int]]
    active_controller: ExtensionSocketController | None = None
    active_event: dict[str, Any] | None = None
    current_loading_timer: TimerContext | None = None

    def __init__(self) -> None:
        self.service = None
        self.socket_path = get_socket_path()
        self.controllers = {}
        self.pending = {}
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
        self.controllers = {}

        def starts_extensions() -> None:
            for controller in ExtensionController.iterate():
                if controller.is_enabled and not controller.has_error:
                    controller.start_detached()

        GLib.idle_add(starts_extensions)

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
            ExtensionSocketController(self.controllers, framer, ext_id)
            # TODO: This is ugly, but we have no other way to detect the extension started successfully
            ExtensionController.create(ext_id).is_running = True
        else:
            logger.debug("Unhandled message received: %s", event)

    def stop(self) -> None:
        if self.service:
            self.service.stop()
            self.service.close()
            self.service = None

    def get_controller_by_keyword(self, keyword: str) -> ExtensionSocketController | None:
        if data_controller := ExtensionController.get_from_keyword(keyword):
            return self.controllers.get(data_controller.id)
        return None

    def _cancel_loading(self) -> None:
        if self.current_loading_timer:
            self.current_loading_timer.cancel()
            self.current_loading_timer = None

    @events.on
    def on_query_change(self) -> None:
        self._cancel_loading()
        self.active_event = None
        self.active_controller = None

    @events.on
    def trigger_event(self, event: dict[str, Any]) -> None:
        if self.active_controller:
            self.active_controller.trigger_event(event)

    @events.on
    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        if controller := ExtensionSocketServer().controllers.get(ext_id):
            for id, new_value in data.get("preferences", {}).items():
                pref = controller.data_controller.user_preferences.get(id)
                if pref and new_value != pref.value:
                    event_data = {"type": "event:update_preferences", "args": [id, new_value, pref.value]}
                    controller.trigger_event(event_data)

    @events.on
    def handle_response(self, response: dict[str, Any], controller: ExtensionSocketController) -> None:
        if not self.active_controller and not self.active_event:
            self.active_event = response.get("event")
            self.active_controller = controller
        elif self.active_controller != controller or self.active_event != response.get("event"):
            # This can happen if the extension was killed from a task manager
            logger.warning("Received response from different controller or event")
            return

        self._cancel_loading()
        events.emit("extension_mode:handle_action", response.get("action"))

    @events.on
    def handle_event(self, event: dict[str, Any], controller: ExtensionSocketController) -> None:
        self._cancel_loading()
        self.current_loading_timer = timer(
            LOADING_DELAY, lambda: events.emit("extension_mode:handle_action", [{"name": "Loading..."}])
        )
        self.active_event = event
        self.active_controller = controller


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    server = ExtensionSocketServer()
    server.start()
