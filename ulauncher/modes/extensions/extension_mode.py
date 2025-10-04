from __future__ import annotations

import asyncio
import contextlib
import html
import logging
from threading import Thread
from typing import Any, Iterator, Literal

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError
from ulauncher.modes.extensions.extension_registry import ExtensionRegistry
from ulauncher.modes.extensions.extension_socket_server import ExtensionSocketServer
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.singleton import Singleton

DEFAULT_ACTION = True  #  keep window open and do nothing
logger = logging.getLogger()
events = EventBus("extensions")


class ExtensionTrigger(Result):
    searchable = True


class ExtensionMode(BaseMode, metaclass=Singleton):
    ext_socket_server: ExtensionSocketServer
    registry: ExtensionRegistry
    active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]] = {}  # keyword: (trigger_id, ext_id)

    def __init__(self) -> None:
        self.registry = ExtensionRegistry()
        self.ext_socket_server = ExtensionSocketServer(self._on_extension_registered)
        self.ext_socket_server.start()
        events.set_self(self)

    def _on_extension_registered(self, ext_id: str) -> None:
        """Callback when an extension successfully registers with the socket server."""
        self.registry.get_or_raise(ext_id).is_running = True

    def handle_query(self, query: Query) -> None:
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)
        if trigger_cache_entry := self._trigger_cache.get(query.keyword, None):
            trigger_id, ext_id = trigger_cache_entry
            self.active_ext = self.ext_socket_server.handle_query(ext_id, trigger_id, query)
        if not trigger_cache_entry or not self.active_ext:
            msg = f"Query not valid for extension mode '{query}'"
            raise RuntimeError(msg)

    @events.on
    def handle_action(self, action_metadata: ActionMetadata | None) -> None:
        if self.active_ext and isinstance(action_metadata, list):
            for result in action_metadata:
                result["icon"] = self.active_ext.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action_metadata)

    def get_triggers(self) -> Iterator[Result]:
        self._trigger_cache.clear()
        for ext in self.registry.iterate():
            if not ext.is_enabled or ext.has_error:
                continue

            for trigger_id, trigger in ext.triggers.items():
                self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)

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
        ext_controllers: list[ExtensionController] = []
        for ext_id in extension_ids:
            with contextlib.suppress(ExtensionNotFoundError):
                ext_controllers.append(self.registry.load(ext_id))

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
