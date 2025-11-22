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
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError
from ulauncher.modes.extensions.extension_socket_server import ExtensionSocketServer
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.singleton import Singleton

DEFAULT_ACTION = True  #  keep window open and do nothing
logger = logging.getLogger()
events = EventBus("extensions")


class ExtensionTrigger(Result):
    searchable = True


class ExtensionMode(BaseMode, metaclass=Singleton):
    """
    Mode that handles extension triggers and communication with extensions.
    Is singleton because it owns the ExtensionSocketServer instance.
    """

    ext_socket_server: ExtensionSocketServer
    active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]] = {}  # keyword: (trigger_id, ext_id)

    def __init__(self) -> None:
        self.ext_socket_server = ExtensionSocketServer()
        self.ext_socket_server.start()
        events.set_self(self)

    def handle_query(self, query: Query) -> None:
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)

        trigger_cache_entry = self._trigger_cache.get(query.keyword, None)

        if trigger_cache_entry:
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
        for ext in extension_registry.iterate():
            if not ext.is_running:
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
            # preview extensions cannot be loaded, so adding them from the registry
            with contextlib.suppress(ExtensionNotFoundError):
                preview_ext = extension_registry.get(ext_id)
                if preview_ext.is_preview:
                    ext_controllers.append(preview_ext)

            with contextlib.suppress(ExtensionNotFoundError):
                # suppress so if an extension is removed, it doesn't try to load it
                ext_controllers.append(extension_registry.load(ext_id))

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
            "[preview] Received preview request for ext_id=%s path=%s debugger=%s",
            ext_id,
            path,
            with_debugger,
        )

        try:
            existing_controller = extension_registry.get(ext_id)
        except ExtensionNotFoundError:
            existing_controller = None
        if existing_controller and existing_controller.is_running:
            logger.info(
                "[preview] Extension '%s' is currently running; stopping it before launching preview version",
                ext_id,
            )
            self.run_ext_batch_job([ext_id], ["stop"], done_msg=f"[preview] Extension '{ext_id}' stopped")
            existing_controller = extension_registry.get(ext_id)  # reload to update is_running state
            existing_controller.shadowed_by_preview = True

        preview_ext_id = f"{ext_id}.preview"
        controller = extension_registry.load(preview_ext_id, path)
        controller.is_preview = True

        # install python dependencies from requirements.txt
        from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies

        deps = ExtensionDependencies(controller.id, controller.path)
        deps.install()

        # Run start_detached instead of start to avoid blocking the main thread
        controller.start_detached(with_debugger=with_debugger)

        logger.info("[preview] Preview extension '%s' started successfully", preview_ext_id)

    @events.on
    def stop_preview(self, payload: dict[str, Any] | None = None) -> None:
        """Handle stopping a preview extension and restoring the previous version if any.

        Expected payload example:
            {
              "preview_ext_id": "my-extension.preview",
              "original_ext_id": "my-extension"
            }
        """
        if not payload or not isinstance(payload, dict):
            logger.error("stop_preview called without valid payload: %s", payload)
            return

        preview_ext_id = payload.get("preview_ext_id")
        original_ext_id = payload.get("original_ext_id")

        if not preview_ext_id or not original_ext_id:
            logger.error("stop_preview called without required fields: %s", payload)
            return

        logger.info(
            "[preview] Received stop preview request for preview_ext_id=%s, original_ext_id=%s",
            preview_ext_id,
            original_ext_id,
        )

        # Stop the preview extension
        stop_msg = f"[preview] Preview extension '{preview_ext_id}' stopped"
        self.run_ext_batch_job([preview_ext_id], ["stop"], done_msg=stop_msg)

        # Try to restart the original extension
        try:
            original_controller = extension_registry.get(original_ext_id)
        except ExtensionNotFoundError:
            original_controller = None
        if original_controller:
            logger.info(
                "[preview] Re-enabling original extension '%s'",
                original_ext_id,
            )
            original_controller.shadowed_by_preview = False
            restart_msg = f"[preview] Original extension '{original_ext_id}' re-enabled"
            self.run_ext_batch_job([original_ext_id], ["start"], done_msg=restart_msg)
