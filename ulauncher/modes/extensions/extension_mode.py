from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Callable, Iterator, Literal, TypedDict

from gi.repository import GLib

from ulauncher.api.shared.event import EventType
from ulauncher.internals import effect_utils, effects
from ulauncher.internals.effects import EffectMessage, EffectType
from ulauncher.internals.query import Query
from ulauncher.internals.result import KeywordTrigger, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()
events = EventBus("extensions")


class ExtensionResponse(TypedDict, total=False):
    interaction_id: int
    keep_app_open: bool
    effect: EffectMessage | list[dict[str, Any]]


class ExtensionLaunchTrigger(Result):
    searchable = True
    ext_id = ""
    trigger_id = ""
    actions = {"__launch__": {"name": "Launch"}}


class ExtensionMode(BaseMode, metaclass=Singleton):
    """
    Mode that handles extension triggers and communication with extensions.
    Is singleton because it owns the ExtensionSocketServer instance.
    """

    active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]] = {}  # keyword: (trigger_id, ext_id)
    _pending_callback: Callable[[EffectMessage | list[Result]], None] | None = None
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

    def handle_query(self, query: Query, callback: Callable[[EffectMessage | list[Result]], None]) -> None:
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)

        if trigger_cache_entry := self._trigger_cache.get(query.keyword, None):
            trigger_id, ext_id = trigger_cache_entry
            if ext := extension_registry.get(ext_id):
                self.active_ext = ext
                event = {
                    "type": EventType.INPUT_TRIGGER,
                    "ext_id": ext.id,
                    "args": [query.argument, trigger_id],
                }

                self.trigger_event(event, callback)
                return

        msg = f"Query not valid for extension mode '{query}'"
        raise RuntimeError(msg)

    def get_triggers(self) -> Iterator[Result]:
        self._trigger_cache.clear()
        for ext in extension_registry.iterate():
            if not ext.is_running:
                continue

            for trigger_id, trigger in ext.triggers.items():
                name = html.escape(trigger.name)
                description = html.escape(trigger.description)
                icon = ext.get_normalized_icon_path(trigger.icon)

                if trigger.keyword:
                    self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)
                    yield KeywordTrigger(name=name, description=description, icon=icon, keyword=trigger.keyword)
                else:
                    yield ExtensionLaunchTrigger(
                        name=name, description=description, icon=icon, ext_id=ext.id, trigger_id=trigger_id
                    )

    def get_placeholder_icon(self) -> str | None:
        if self.active_ext:
            return self.active_ext.get_normalized_icon_path()
        return None

    def activate_result(
        self,
        action_id: str,
        result: Result,
        _query: Query,
        callback: Callable[[EffectMessage | list[Result]], None],
    ) -> None:
        effect_msg: EffectMessage | list[Result] = effects.close_window()
        if action_id == "__legacy_on_enter__" and result.on_enter:
            effect_msg = result.on_enter
        elif action_id == "__legacy_on_alt_enter__" and result.on_alt_enter:
            effect_msg = result.on_alt_enter
        elif action_id == "__launch__" and isinstance(result, ExtensionLaunchTrigger):
            self.trigger_event(
                {
                    "type": EventType.LAUNCH_TRIGGER,
                    "args": [result.trigger_id],
                    "ext_id": result.ext_id,
                },
                callback,
            )
            return
        else:
            event_type = EventType.RESULT_ACTIVATION
            event_args = [action_id, result]
            self.trigger_event({"type": event_type, "args": event_args}, callback)
            return

        if isinstance(effect_msg, dict) and effect_msg.get("type") == EffectType.LEGACY_ACTIVATE_CUSTOM:
            self.trigger_event({**effect_msg, "type": EventType.LEGACY_ACTIVATE_CUSTOM}, callback)
            return

        callback(effect_msg)

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

    def trigger_event(self, event: dict[str, Any], callback: Callable[[EffectMessage | list[Result]], None]) -> None:
        self._interaction_id += 1
        self._pending_callback = callback
        event["interaction_id"] = self._interaction_id

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
    def handle_message(self, ext_id: str, name: str, *args: Any) -> None:
        logger.debug('Incoming %s message with arguments "%s" from "%s"', name, args, ext_id)
        if not args:
            logger.warning("Received '%s' message without event payload from %s", name, ext_id)
            return
        if name == "response":
            self.handle_response(ext_id, args[0])
        elif name == "clipboard_store":
            events.emit("app:clipboard_store", args[0])
        else:
            logger.warning("Received unknown message from %s: %s", ext_id, name)

    def handle_response(self, ext_id: str, response: ExtensionResponse) -> None:
        if not self.active_ext:
            logger.error("No active extension to handle response")
            return
        if self.active_ext.id != ext_id:
            logger.debug("Ignoring response from inactive extension %s", ext_id)
            return
        if not self._pending_callback or response.get("interaction_id") != self._interaction_id:
            logger.debug("Ignoring outdated extension response")
            return

        raw_effect_msg = response.get("effect", effects.close_window())
        effect_msg: EffectMessage | list[Result]

        if isinstance(raw_effect_msg, list):
            effect_msg = []
            for result_dict in raw_effect_msg:
                result = Result(**result_dict)
                result.icon = self.active_ext.get_normalized_icon_path(result_dict.get("icon")) or ""

                # Convert legacy actions to the new actions dictionary format
                if not result.actions:
                    if "on_enter" in result:
                        result.actions["__legacy_on_enter__"] = {"name": "Main action"}
                    if "on_alt_enter" in result:
                        result.actions["__legacy_on_alt_enter__"] = {"name": "Secondary action"}

                effect_msg.append(result)

        elif not response.get("keep_app_open", True):
            effect_utils.handle(raw_effect_msg, prevent_close=True)
            effect_msg = effects.close_window()

        else:
            effect_msg = raw_effect_msg

        self._pending_callback(effect_msg)
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
