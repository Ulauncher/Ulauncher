from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Callable, Iterator, Literal, TypedDict

from ulauncher.api.shared.event import EventType
from ulauncher.internals import effect_utils, effects
from ulauncher.internals.effects import EffectMessage, EffectType
from ulauncher.internals.query import Query
from ulauncher.internals.result import KeywordTrigger, Result
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionControllerTrigger,
    preview,
)
from ulauncher.modes.mode import Mode
from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.socket_msg_controller import summarize_ipc_args

logger = logging.getLogger(__name__)
events = EventBus("extensions")

LOADING_TIMEOUT = 10  # seconds to wait for a transitioning extension before giving up


class ExtensionResponse(TypedDict, total=False):
    request_id: int
    keep_app_open: bool
    effect: EffectMessage | list[dict[str, Any]]


class ExtensionLaunchTrigger(Result):
    searchable = True
    ext_id = ""
    trigger_id = ""
    actions = {"__launch__": {"name": "Launch"}}


class ExtensionMode(Mode):
    """Mode that handles extension triggers and communication with extensions."""

    _active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]]  # keyword: (trigger_id, ext_id)
    _pending_callback: Callable[[EffectMessage | list[Result]], None] | None = None
    _loading_timer: scheduling.Context | None = None
    _request_id: int = 0

    def __init__(self) -> None:
        self._trigger_cache = {}
        events.set_self(self)
        scheduling.run_when_idle(self.start_extensions)

    def start_extensions(self) -> None:
        for ext in extension_registry.load_all():
            if ext.state.is_enabled:
                ext.start()

    def has_trigger_changes(self) -> bool:
        return not self._trigger_cache

    @events.on
    def invalidate_cache(self) -> None:
        self._trigger_cache.clear()

    @events.on
    def errored(self, ext_id: str) -> None:
        if not self.active_ext or self.active_ext.id != ext_id:
            return
        if self._loading_timer:
            self._finish_loading()
        else:
            self._pending_callback = None

    @events.on
    def started(self, ext_id: str) -> None:
        # start() runs in a worker thread, so re-evaluate the query on the main loop.
        if self.active_ext and self.active_ext.id == ext_id:
            scheduling.run_when_idle(lambda: events.emit("app:reload_query"))

    @property
    def active_ext(self) -> ExtensionController | None:
        return self._active_ext

    @active_ext.setter
    def active_ext(self, ext: ExtensionController | None) -> None:
        if ext is not self._active_ext:
            self._pending_callback = None
            self._active_ext = ext

    def handle_query(self, query: Query, callback: Callable[[EffectMessage | list[Result]], None]) -> None:
        self._clear_loading_timer()
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)

        self._ensure_trigger_cache()
        trigger_cache_entry = self._trigger_cache.get(query.keyword, None)
        ext = extension_registry.get(trigger_cache_entry[1]) if trigger_cache_entry else None
        if not trigger_cache_entry or not ext:
            # Core only routes a keyword here when its own cache claims this mode owns it, so a miss
            # means the two caches disagree (e.g. the extension was removed since core last loaded).
            logger.warning("Extension query '%s' did not match any enabled extension", query)
            callback([])
            return

        self.active_ext = ext
        if not ext.is_running:
            # Transitioning (restart/preview/update/startup): wait for it to come up. Returning
            # without a result lets core show "Loading..." after PLACEHOLDER_DELAY, and `started`
            # re-runs the query once the extension is ready. The wait ends early if the extension
            # exits with an error, otherwise after LOADING_TIMEOUT.
            self._pending_callback = callback
            self._loading_timer = scheduling.timer(LOADING_TIMEOUT, self._finish_loading)
            return

        self.send_request(
            {"type": EventType.INPUT_TRIGGER, "ext_id": ext.id, "args": [query.argument, trigger_cache_entry[0]]},
            callback,
        )

    def _iter_enabled_triggers(self) -> Iterator[tuple[ExtensionController, str, ExtensionControllerTrigger]]:
        for ext in extension_registry.iterate():
            if not ext.is_enabled:
                continue
            for trigger_id, trigger in ext.triggers.items():
                yield ext, trigger_id, trigger

    def _ensure_trigger_cache(self) -> None:
        if not self._trigger_cache:
            for ext, trigger_id, trigger in self._iter_enabled_triggers():
                if trigger.keyword:
                    self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)

    def _clear_loading_timer(self) -> None:
        if self._loading_timer:
            self._loading_timer.cancel()
            self._loading_timer = None

    def _finish_loading(self) -> None:
        """Resolve a pending loading wait with empty results (no-op if not waiting)."""
        self._clear_loading_timer()
        callback, self._pending_callback = self._pending_callback, None
        if callback:
            callback([])

    def get_triggers(self) -> Iterator[Result]:
        self._trigger_cache.clear()
        for ext, trigger_id, trigger in self._iter_enabled_triggers():
            name = html.escape(trigger.name)
            description = html.escape(trigger.description)
            icon = ext.get_icon_value(trigger.icon)

            if trigger.keyword:
                self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)
                yield KeywordTrigger(name=name, description=description, icon=icon, keyword=trigger.keyword)
            else:
                yield ExtensionLaunchTrigger(
                    name=name, description=description, icon=icon, ext_id=ext.id, trigger_id=trigger_id
                )

    def get_placeholder_icon(self) -> str | None:
        if self.active_ext:
            return self.active_ext.get_icon_value()
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
            self.send_request(
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
            self.send_request({"type": event_type, "args": event_args}, callback)
            return

        if isinstance(effect_msg, dict) and effect_msg.get("type") == EffectType.LEGACY_ACTIVATE_CUSTOM:
            self.send_request({**effect_msg, "type": EventType.LEGACY_ACTIVATE_CUSTOM}, callback)
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
            old_preferences = data.get("old_preferences", {})
            for p_id, new_value in data.get("preferences", {}).items():
                pref = ext.preferences.get(p_id)
                old_value = old_preferences.get(p_id, pref.value if pref else None)
                if pref and new_value != old_value:
                    event_data = {"type": EventType.UPDATE_PREFERENCES, "args": [p_id, new_value, old_value]}
                    ext.send_message(event_data)

    def send_request(self, event: dict[str, Any], callback: Callable[[EffectMessage | list[Result]], None]) -> None:
        """
        Send an event to the extension, expecting a response (passed to the callback).
        The event is enriched with a request_id property, used to filter out stale responses.

        For one-off messages, use ext.send_message() directly instead.
        """
        # If active_ext is not set (e.g., for launch triggers, without keywords),
        # try to get it from the event's ext_id
        if not self.active_ext:
            ext_id = event.get("ext_id")
            if ext_id:
                self.active_ext = extension_registry.get(ext_id)

        if not self.active_ext:
            logger.error("No active extension to send event to")
            return

        if not self.active_ext.is_running:
            logger.warning("Cannot send event to inactive extension %s", self.active_ext.id)
            return

        self._request_id += 1
        self._pending_callback = callback
        event["request_id"] = self._request_id
        self.active_ext.send_message(event)

    @events.on
    def handle_message(self, ext_id: str, name: str, *args: Any) -> None:
        logger.debug("Incoming %s message with arguments %s from %r", name, summarize_ipc_args(args), ext_id)
        if not args:
            logger.warning("Received '%s' message without event payload from %s", name, ext_id)
            return
        if name == "response":
            self.handle_response(ext_id, args[0])
        elif name == "clipboard_store":
            # Extension API: only copies; the launcher stays open and the extension is
            # responsible for any subsequent UI changes.
            events.emit("app:clipboard_store", args[0])
        elif name == "notify":
            ext = extension_registry.get(ext_id)
            if not ext:
                logger.warning("Notification sent from an extension, '%s', which was not found", ext_id)
                return
            try:
                body, notification_id = args
            except ValueError:
                logger.warning("notify expects two arguments, got %s from %s", len(args), ext_id)
            else:
                events.emit(
                    "app:show_notification",
                    f"ext-{ext.id}-{notification_id}",
                    f"Message from {ext.manifest.name} extension",
                    body,
                )
        else:
            logger.warning("Received unknown message from %s: %s", ext_id, name)

    def handle_response(self, ext_id: str, response: ExtensionResponse) -> None:
        if not self.active_ext:
            logger.error("No active extension to handle response")
            return
        if self.active_ext.id != ext_id:
            logger.debug("Ignoring response from inactive extension %s", ext_id)
            return
        if not self._pending_callback or response.get("request_id") != self._request_id:
            logger.debug("Ignoring outdated extension response")
            return

        raw_effect_msg = response.get("effect", effects.close_window())
        effect_msg: EffectMessage | list[Result]

        if isinstance(raw_effect_msg, list):
            effect_msg = []
            for result_dict in raw_effect_msg:
                result = Result(**result_dict)
                result.icon = self.active_ext.get_icon_value(result_dict.get("icon"))

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
    def preview_ext(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        """Run an extension from a dev path WITHOUT installing it. Triggered from the CLI via D-Bus.

        While the preview is active, the controller with this id launches from the dev path; its
        dependencies are installed by the CLI before this is called.
        """

        logger.info("[preview] Previewing ext_id=%s path=%s debugger=%s", ext_id, path, with_debugger)
        preview.set(ext_id, path, with_debugger)

        # Register a controller so a not-yet-installed extension's triggers become available; an
        # installed one already has one (now launching from the preview path). Restart it so a
        # background-running installed instance relaunches from the dev path.
        extension_registry.get(ext_id) or extension_registry.load(ext_id, path)

        # Guard the restart against a stop_preview that races in during the stop: only relaunch if
        # this preview is still the active one, otherwise stop_preview owns restoring the extension.
        def start_if_still_previewing() -> None:
            if preview.ext_id == ext_id:
                self.run_ext_batch_job([ext_id], ["start"])

        self.run_ext_batch_job([ext_id], ["stop"], callback=start_if_still_previewing)

    @events.on
    def stop_preview(self) -> None:
        """Stop the active preview and restore the installed extension. Triggered from the CLI via D-Bus"""

        # The CLI sends this on Ctrl+C even when preview_ext was never delivered (e.g. interrupted
        # mid dependency-install), in which case there is no preview to stop or extension to restore.
        ext_id = preview.ext_id
        if not ext_id:
            logger.debug("[preview] Ignoring stop_preview; no preview active")
            return

        logger.info("[preview] Stopping preview %s", ext_id)
        preview.clear()

        def restore_original() -> None:
            # Reload from the installed path, or drop the controller if the extension was never installed.
            controller = extension_registry.load(ext_id)
            if controller and controller.is_enabled:
                self.run_ext_batch_job([ext_id], ["start"])

        self.run_ext_batch_job([ext_id], ["stop"], callback=restore_original)
