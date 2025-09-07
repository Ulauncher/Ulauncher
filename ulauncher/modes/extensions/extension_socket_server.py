from __future__ import annotations

import asyncio
import logging
import os
from threading import Thread
from typing import Any, Literal

from gi.repository import Gio, GLib, GObject

from ulauncher.internals.query import Query
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
    socket_controllers: dict[str, ExtensionSocketController]
    pending: dict[int, tuple[JSONFramer, int, int]]
    active_socket_controller: ExtensionSocketController | None = None
    active_event: dict[str, Any] | None = None
    current_loading_timer: TimerContext | None = None

    def __init__(self) -> None:
        self.service = None
        self.socket_path = get_socket_path()
        self.socket_controllers = {}
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
        self.socket_controllers = {}

        def start_extensions() -> None:
            for ext_controller in ExtensionController.iterate():
                if ext_controller.is_enabled and not ext_controller.has_error:
                    ext_controller.start_detached()

        GLib.idle_add(start_extensions)

    def handle_query(self, query: Query) -> str | None:
        """
        Derives the extension belonging to a user query, handles the query and returns the extension id
        :returns: ext_id of the extension that will handle this query
        """
        socket_controller: ExtensionSocketController | None = None
        if query.keyword:
            self.on_query_change()
            if socket_controller := self.get_controller_by_keyword(query.keyword):
                socket_controller.handle_query(query)
                return socket_controller.ext_id
        return None

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
        if ext_controller := ExtensionController.get_from_keyword(keyword):
            return self.socket_controllers.get(ext_controller.id)
        return None

    def _cancel_loading(self) -> None:
        if self.current_loading_timer:
            self.current_loading_timer.cancel()
            self.current_loading_timer = None

    def on_query_change(self) -> None:
        self._cancel_loading()
        self.active_event = None
        self.active_socket_controller = None

    @events.on
    def trigger_event(self, event: dict[str, Any]) -> None:
        ext_id = event.get("ext_id")
        socket_controller = self.socket_controllers.get(ext_id) if ext_id else self.active_socket_controller
        if socket_controller:
            socket_controller.trigger_event(event)

    @events.on
    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        if socket_controller := self.socket_controllers.get(ext_id):
            for p_id, new_value in data.get("preferences", {}).items():
                pref = socket_controller.ext_controller.preferences.get(p_id)
                if pref and new_value != pref.value:
                    event_data = {"type": "event:update_preferences", "args": [p_id, new_value, pref.value]}
                    socket_controller.trigger_event(event_data)

    @events.on
    def handle_response(self, response: dict[str, Any], socket_controller: ExtensionSocketController) -> None:
        if not self.active_socket_controller and not self.active_event:
            self.active_event = response.get("event")
            self.active_socket_controller = socket_controller
        elif self.active_socket_controller != socket_controller or self.active_event != response.get("event"):
            # This can happen if the extension was killed from a task manager
            logger.warning("Received response from different controller or event")
            return

        self._cancel_loading()
        events.emit("extension_mode:handle_action", response.get("action"))

    @events.on
    def handle_event(self, event: dict[str, Any], socket_controller: ExtensionSocketController) -> None:
        self._cancel_loading()
        self.current_loading_timer = timer(
            LOADING_DELAY, lambda: events.emit("extension_mode:handle_action", [{"name": "Loading..."}])
        )
        self.active_event = event
        self.active_socket_controller = socket_controller

    def run_ext_batch_job(
        self, extension_ids: list[str], jobs: list[Literal["start", "stop"]], done_msg: str | None = None
    ) -> None:
        ext_controllers = [ExtensionController.create(ext_id) for ext_id in extension_ids]

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    await asyncio.gather(*[c.start() for c in ext_controllers if c.is_enabled])
                elif job == "stop":
                    await asyncio.gather(*[c.stop() for c in ext_controllers])

        def run_batch() -> None:
            asyncio.run(run_batch_async())

        Thread(target=run_batch).start()

        logger.info(done_msg)

    @events.on
    def reload_ext(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop", "start"], done_msg=f"{len(extension_ids)} extensions (re)loaded")

    @events.on
    def stop_ext(self, extension_ids: list[str] | None = None) -> None:
        if not extension_ids:
            logger.warning("Stop message received without any extension IDs. No extensions will be stopped.")
            return

        logger.info("Stopping extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop"], done_msg=f"{len(extension_ids)} extensions stopped")
