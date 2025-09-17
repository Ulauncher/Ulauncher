from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Iterator, Literal

from gi.repository import GLib

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_socket_server import ExtensionSocketServer
from ulauncher.utils.eventbus import EventBus

DEFAULT_ACTION = True  #  keep window open and do nothing
logger = logging.getLogger()
events = EventBus("extensions")


class ExtensionTrigger(Result):
    searchable = True


class ExtensionMode(BaseMode):
    """
    Mode that handles extensions.
    Singleton class so that we have only one instance of the extension socket server.
    """

    _instance: ExtensionMode | None = None
    ext_socket_server: ExtensionSocketServer
    active_ext_id: str | None = None
    controllers: dict[str, ExtensionController] = {}

    def __new__(cls) -> ExtensionMode:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Only initialize once
        if hasattr(self, "_initialized"):
            return

        # Ideally, constructors should not have side effects.
        # TODO: Review client code that relies on this behavior.
        self.ext_socket_server = ExtensionSocketServer(self.on_extension_registered_callback)
        self.ext_socket_server.start()
        events.set_self(self)
        GLib.idle_add(self.start_extensions)

        self._initialized = True

    def start_extensions(self) -> None:
        for ext_controller in ExtensionController.create_all_installed():
            if ext_controller.is_enabled and not ext_controller.has_error:
                ext_controller.start_detached()
            self.controllers[ext_controller.id] = ext_controller

    def handle_query(self, query: Query) -> None:
        ext_id = ""

        for controller in self.controllers.values():
            for trigger in controller.triggers.values():
                if controller.is_running and query.keyword and query.keyword == trigger.keyword:
                    ext_id = controller.id
                    break

        if not ext_id:
            return

        if not self.ext_socket_server.handle_query(ext_id, query):
            msg = f"Query not valid for extension mode {query}"
            raise RuntimeError(msg)

        return

    def on_extension_registered_callback(self, ext_id: str) -> None:
        "Is fired when an extension registers itself with the socket server."
        logger.debug("Extension registered: %s", ext_id)
        if controller := self.controllers.get(ext_id):
            controller.is_running = True

    @events.on
    def handle_action(self, action_metadata: ActionMetadata | None) -> None:
        if self.active_ext_id and isinstance(action_metadata, list):
            controller = ExtensionController.create_from_id(self.active_ext_id)
            for result in action_metadata:
                result["icon"] = controller.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action_metadata)

    def get_triggers(self) -> Iterator[Result]:
        for ext in ExtensionController.create_all_installed():
            if not ext.is_enabled:
                continue

            for trigger_id, trigger in ext.triggers.items():
                action = (
                    f"{trigger.keyword} "
                    if trigger.keyword
                    else {
                        "type": "action:launch_trigger",
                        "args": [trigger_id],
                        "ext_id": ext.id,
                    }
                )

                yield ExtensionTrigger(
                    name=html.escape(trigger.name),
                    description=html.escape(trigger.description),
                    icon=ext.get_normalized_icon_path(trigger.icon),
                    keyword=trigger.keyword,
                    on_enter=action,
                )

    def activate_result(self, result: Result, query: Query, alt: bool) -> ActionMetadata:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """
        handler = getattr(result, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler

    def run_ext_batch_job(
        self, extension_ids: list[str], jobs: list[Literal["start", "stop"]], done_msg: str | None = None
    ) -> None:
        ext_controllers = [ExtensionController.create_from_id(ext_id) for ext_id in extension_ids]

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    await asyncio.gather(*[c.start() for c in ext_controllers if c and c.is_enabled])
                elif job == "stop":
                    await asyncio.gather(*[c.stop() for c in ext_controllers if c])

        def run_batch() -> None:
            asyncio.run(run_batch_async())

        Thread(target=run_batch).start()

        logger.info(done_msg)

    @events.on
    def reload(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop", "start"], done_msg=f"{len(extension_ids)} extensions (re)loaded")

    @events.on
    def stop(self, extension_ids: list[str] | None = None) -> None:
        if not extension_ids:
            logger.warning("Stop message received without any extension IDs. No extensions will be stopped.")
            return

        logger.info("Stopping extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop"], done_msg=f"{len(extension_ids)} extensions stopped")

    @events.on
    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        self.ext_socket_server.update_preferences(ext_id, data)

    @events.on
    def trigger_event(self, event: dict[str, Any]) -> None:
        self.ext_socket_server.trigger_event(event)

    @events.on
    def handle_response(self, ext_id: str, response: dict[str, Any]) -> None:
        self.ext_socket_server.handle_response(ext_id, response)

    @events.on
    def preview_ext(self, payload: dict[str, Any] | None = None) -> None:
        """Handle a preview extension request coming from the CLI (via D-Bus).

        Stage: run the extension from an arbitrary filesystem path WITHOUT installing it.

        Expected payload example:
            {
              "ext_id": "my-extension",
              "path": "/abs/path/to/extension",
              "with_debugger": false
            }
        """
        if not payload or not isinstance(payload, dict):  # basic guard
            logger.error("preview_ext called without valid payload: %s", payload)
            return

        ext_id = payload.get("ext_id")
        path = payload.get("path")
        with_debugger = bool(payload.get("with_debugger"))
        assert ext_id, "preview_ext called without ext_id"
        assert path, "preview_ext called without path"

        logger.info(
            "[preview] Received preview request for ext_id=%s path=%s debugger=%s (stub stage)",
            ext_id,
            path,
            with_debugger,
        )

        existing_controller = ExtensionController.create_from_id(ext_id)
        if existing_controller and existing_controller.is_running:
            logger.info(
                "[preview] Extension '%s' is currently running; stopping it before launching preview version",
                ext_id,
            )
            self.run_ext_batch_job([ext_id], ["stop"], done_msg=f"[preview] Extension '{ext_id}' stopped")

        preview_ext_id = f"{ext_id}.preview"
        controller = ExtensionController(preview_ext_id, path)
        self.controllers[preview_ext_id] = controller
        controller.is_preview = True
        asyncio.run(controller.install())
        asyncio.run(controller.start())
