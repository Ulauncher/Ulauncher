from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Callable, Iterator, Literal, cast

from gi.repository import GLib

from ulauncher.api.shared.event import EventType
from ulauncher.internals import actions
from ulauncher.internals.actions import ActionMessage
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()
events = EventBus("extensions")

# Maps action types that require async extension communication to their event types
ASYNC_ACTION_TYPES = {
    "action:activate_custom": EventType.ACTIVATE_CUSTOM,
    "action:launch_trigger": EventType.LAUNCH_TRIGGER,
}


class ExtensionTrigger(Result):
    searchable = True


class ExtensionMode(BaseMode, metaclass=Singleton):
    """
    Mode that handles extension triggers and communication with extensions.
    Is singleton because it owns the ExtensionSocketServer instance.
    """

    active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]] = {}  # keyword: (trigger_id, ext_id)
    _pending_callback: Callable[[ActionMessage | list[Result]], None] | None = None
    _interaction_id: int = 0

    def __init__(self) -> None:
        events.set_self(self)
        GLib.idle_add(self.start_extensions)

    def start_extensions(self) -> None:
        for ext in extension_registry.load_all():
            if ext.is_enabled and not ext.has_error:
                ext.start()
                # legacy_preferences_load is useless and deprecated
                prefs = {p_id: pref.value for p_id, pref in ext.preferences.items()}
                ext.send_message({"type": EventType.LEGACY_PREFERENCES_LOAD, "args": [prefs]})

    def has_trigger_changes(self) -> bool:
        return not self._trigger_cache

    @events.on
    def invalidate_cache(self) -> None:
        self._trigger_cache.clear()

    def handle_query(self, query: Query, callback: Callable[[ActionMessage | list[Result]], None]) -> None:
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)

        self._interaction_id += 1

        self._pending_callback = callback

        if trigger_cache_entry := self._trigger_cache.get(query.keyword, None):
            trigger_id, ext_id = trigger_cache_entry
            self.active_ext = extension_registry.get(ext_id)
            if self.active_ext:
                event = {
                    "type": EventType.INPUT_TRIGGER,
                    "ext_id": self.active_ext.id,
                    "args": [query.argument, trigger_id],
                    "interaction_id": self._interaction_id,
                }

                self.active_ext.debounced_send_message(event)
                return

        msg = f"Query not valid for extension mode '{query}'"
        raise RuntimeError(msg)

    def get_triggers(self) -> Iterator[Result]:
        self._trigger_cache.clear()
        for ext in extension_registry.iterate():
            if not ext.is_running:
                continue

            for trigger_id, trigger in ext.triggers.items():
                self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)

                action: actions.ActionMessage = (
                    actions.set_query(f"{trigger.keyword} ")
                    if trigger.keyword
                    else cast(
                        "actions.LaunchTriggerAction",
                        {
                            "type": "action:launch_trigger",
                            "args": [trigger_id],
                            "ext_id": ext.id,
                        },
                    )
                )

                yield ExtensionTrigger(
                    name=html.escape(trigger.name),
                    description=html.escape(trigger.description),
                    icon=ext.get_normalized_icon_path(trigger.icon),
                    keyword=trigger.keyword,
                    on_enter=action,
                )

    def get_placeholder_icon(self) -> str | None:
        if self.active_ext:
            return self.active_ext.get_normalized_icon_path()
        return None

    def activate_result(
        self, result: Result, _query: Query, alt: bool, callback: Callable[[ActionMessage | list[Result]], None]
    ) -> None:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """

        action_msg = result.on_alt_enter if alt else result.on_enter
        if (
            isinstance(action_msg, dict)
            and (action_type := action_msg.get("type", ""))
            and (evt_type := ASYNC_ACTION_TYPES.get(action_type))
        ):
            # for async flow, set up the callback, trigger an extension event and wait for the response
            self._interaction_id += 1
            self._pending_callback = callback
            return_msg = {
                **action_msg,
                "type": evt_type,
                "interaction_id": self._interaction_id,
            }
            self.trigger_event(return_msg)
            return

        callback(actions.do_nothing() if action_msg is None else action_msg)

    def run_ext_batch_job(
        self, extension_ids: list[str], jobs: list[Literal["start", "stop"]], callback: Callable[[], None] | None = None
    ) -> None:
        ext_controllers: list[ExtensionController] = []
        for ext_id in extension_ids:
            if ext := extension_registry.get(ext_id) or extension_registry.load(ext_id):
                ext_controllers.append(ext)  # noqa: PERF401

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    for controller in ext_controllers:
                        if controller.is_enabled:
                            controller.start()
                elif job == "stop":
                    await asyncio.gather(*[c.stop() for c in ext_controllers])

        def run_batch() -> None:
            asyncio.run(run_batch_async())
            if callback:
                callback()

        Thread(target=run_batch).start()

    @events.on
    def reload(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(
            extension_ids,
            ["stop", "start"],
            callback=lambda: logger.info("%s extensions (re)loaded", len(extension_ids)),
        )

    @events.on
    def stop(self, extension_ids: list[str] | None = None) -> None:
        if not extension_ids:
            logger.warning("Stop message received without any extension IDs. No extensions will be stopped.")
            return

        logger.info("Stopping extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(
            extension_ids, ["stop"], callback=lambda: logger.info("%s extensions stopped", len(extension_ids))
        )

    @events.on
    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        if ext := extension_registry.get(ext_id):
            for p_id, new_value in data.get("preferences", {}).items():
                pref = ext.preferences.get(p_id)
                if pref and new_value != pref.value:
                    event_data = {"type": EventType.UPDATE_PREFERENCES, "args": [p_id, new_value, pref.value]}
                    ext.send_message(event_data)

    def trigger_event(self, event: dict[str, Any]) -> None:
        # If active_ext is not set (e.g., for launch triggers, without keywords),
        # try to get it from the event's ext_id
        if not self.active_ext:
            ext_id = event.get("ext_id")
            if ext_id:
                self.active_ext = extension_registry.get(ext_id)

        if not self.active_ext:
            logger.error("No active extension to send event to")
            return
        self.active_ext.send_message(event)

    @events.on
    def handle_response(self, ext_id: str, response: dict[str, Any]) -> None:
        if not self.active_ext:
            logger.error("No active extension to handle response")
            return
        if self.active_ext.id != ext_id:
            logger.debug("Ignoring response from inactive extension %s", ext_id)
            return
        if not self._pending_callback or response.get("event", {}).get("interaction_id") != self._interaction_id:
            logger.debug("Ignoring outdated extension response")
            return

        action_msg: ActionMessage | list[Result] = response.get("action", actions.do_nothing())

        if isinstance(action_msg, list):
            for result in action_msg:
                result["icon"] = self.active_ext.get_normalized_icon_path(result.get("icon"))

            action_msg = [Result(**res) for res in action_msg]

        elif not response.get("event", {}).get("keep_app_open", True):
            action_msg = actions.action_list([action_msg, actions.close_window()])

        self._pending_callback(action_msg)
        self._pending_callback = None

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

        def load_preview_extension(ext_id: str) -> None:
            preview_ext_id = f"{ext_id}.preview"
            if controller := extension_registry.load(preview_ext_id, path):
                controller.is_preview = True

                # install python dependencies from requirements.txt
                from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies

                deps = ExtensionDependencies(controller.id, controller.path)
                deps.install()

                controller.start(with_debugger=with_debugger)

                logger.info("[preview] Preview extension '%s' started successfully", preview_ext_id)

        def on_stopped(ext_id: str) -> None:
            logger.info("[preview] Extension '%s' stopped", ext_id)
            if existing_controller := extension_registry.get(ext_id):  # reload to update is_running state
                existing_controller.shadowed_by_preview = True
            load_preview_extension(ext_id)

        existing_controller = extension_registry.get(ext_id)
        if existing_controller and existing_controller.is_running:
            logger.info(
                "[preview] Extension '%s' is currently running; stopping it before launching preview version",
                ext_id,
            )
            self.run_ext_batch_job([ext_id], ["stop"], callback=lambda: on_stopped(ext_id))
        else:
            load_preview_extension(ext_id)

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

        # Try to restart the original extension
        def restart_original_extension(ext_id: str) -> None:
            ext = extension_registry.get(ext_id)
            if ext:
                logger.info(
                    "[preview] Re-enabling original extension '%s'",
                    ext_id,
                )
                ext.shadowed_by_preview = False
                restart_msg = f"[preview] Original extension '{ext_id}' re-enabled"
                self.run_ext_batch_job([ext_id], ["start"], callback=lambda: logger.info(restart_msg))

        def stopped_handler(original_ext_id: str) -> None:
            logger.info("[preview] Preview extension stopped. Restarting %s", original_ext_id)
            restart_original_extension(original_ext_id)

        # Stop the preview extension
        self.run_ext_batch_job([preview_ext_id], ["stop"], lambda: stopped_handler(original_ext_id))
