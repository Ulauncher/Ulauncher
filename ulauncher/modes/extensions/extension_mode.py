from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Iterator, Literal

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
    ext_socket_server: ExtensionSocketServer
    active_ext_id: str | None = None

    def __init__(self) -> None:
        self.ext_socket_server = ExtensionSocketServer()
        self.ext_socket_server.start()
        events.set_self(self)

    def handle_query(self, query: Query) -> None:
        self.active_ext_id = self.ext_socket_server.handle_query(query)
        if not self.active_ext_id:
            msg = f"Query not valid for extension mode {query}"
            raise RuntimeError(msg)

    @events.on
    def handle_action(self, action_metadata: ActionMetadata | None) -> None:
        if self.active_ext_id and isinstance(action_metadata, list):
            controller = ExtensionController(self.active_ext_id)
            for result in action_metadata:
                result["icon"] = controller.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action_metadata)

    def get_triggers(self) -> Iterator[Result]:
        for ext in ExtensionController.iterate():
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
