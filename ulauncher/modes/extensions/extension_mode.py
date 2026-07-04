from __future__ import annotations

import html
import logging
from typing import Callable, Iterator

from ulauncher.api.shared.event import EventType
from ulauncher.internals import effect_utils, effects, ipc
from ulauncher.internals.effects import EffectMessage, EffectType
from ulauncher.internals.query import Query
from ulauncher.internals.result import KeywordTrigger, Result
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionControllerTrigger,
)
from ulauncher.modes.extensions.extension_service import ext_service
from ulauncher.modes.mode import Mode
from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.socket_msg_controller import summarize_ipc_args

logger = logging.getLogger(__name__)
events = EventBus("extensions", skip_if_not_bound=True)

LOADING_TIMEOUT = 10  # seconds to wait for a transitioning extension before giving up


class ExtensionLaunchTrigger(Result):
    searchable = True
    ext_id = ""
    trigger_id = ""
    actions = {"__launch__": {"name": "Launch"}}


class ExtensionMode(Mode):
    """Mode that handles extension triggers and communication with extensions."""

    _active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]]  # keyword: (trigger_id, ext_id)
    _pending_callback: Callable[[EffectMessage], None] | None = None
    _loading_timer: scheduling.Context | None = None
    _request_id: int = 0

    def __init__(self) -> None:
        ext_service.activate()
        self._trigger_cache = {}
        events.set_self(self)

    def has_trigger_changes(self) -> bool:
        return not self._trigger_cache

    @events.on
    def invalidate_cache(self) -> None:
        self._trigger_cache.clear()

    @events.on
    def errored(self, ext_id: str) -> None:
        if not self._active_ext or self._active_ext.id != ext_id:
            return
        if self._loading_timer:
            self._finish_loading([self._loading_failed_result()])
        else:
            self._pending_callback = None

    @events.on
    def started(self, ext_id: str) -> None:
        # start() runs in a worker thread, so re-evaluate the query on the main loop.
        if self._active_ext and self._active_ext.id == ext_id:
            scheduling.run_when_idle(lambda: events.emit("app:reload_query"))

    def handle_query(self, query: Query, callback: Callable[[EffectMessage], None]) -> None:
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
            callback(effects.render_results([Result(name="Extension not available")]))
            return

        self._active_ext = ext
        if not ext.owns_runtime:
            # Transitioning (restart/preview/update/startup): wait for it to come up. Returning
            # without a result lets core show "Loading..." after PLACEHOLDER_DELAY, and `started`
            # re-runs the query once the extension is ready. The wait ends with a failure message if
            # the extension exits with an error, otherwise empty after LOADING_TIMEOUT.
            self._pending_callback = callback
            self._loading_timer = scheduling.timer(LOADING_TIMEOUT, self._finish_loading)
            return

        event: ipc.InputTriggerEvent = {
            "type": EventType.INPUT_TRIGGER,
            "args": (query.argument, trigger_cache_entry[0]),
        }
        self._send_request(event, callback)

    def _iter_enabled_triggers(self) -> Iterator[tuple[ExtensionController, str, ExtensionControllerTrigger]]:
        for ext in extension_registry.iterate(sort=True):
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

    def _finish_loading(self, results: list[Result] | None = None) -> None:
        """Resolve a pending loading wait, defaulting to empty results (no-op if not waiting)."""
        self._clear_loading_timer()
        callback, self._pending_callback = self._pending_callback, None
        if callback:
            callback(effects.render_results(results or []))

    def _loading_failed_result(self) -> Result:
        ext = self._active_ext
        name = (ext.manifest.name if ext else "") or "Extension"
        # A preview's error isn't persisted (it surfaces in the preview's own console), so the
        # stored message is only meaningful for an installed extension that errored.
        description = ext.state.error_message if ext and ext.has_error else ""
        icon = ext.get_icon_value() if ext else None
        return Result(name=f"{name} failed to start", description=description, icon=icon)

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
        if self._active_ext:
            return self._active_ext.get_icon_value()
        return None

    def activate_result(
        self,
        action_id: str,
        result: Result,
        _query: Query,
        callback: Callable[[EffectMessage], None],
    ) -> None:
        effect_msg: EffectMessage = effects.close_window()
        if action_id == "__legacy_on_enter__" and result.on_enter:
            effect_msg = result.on_enter
        elif action_id == "__legacy_on_alt_enter__" and result.on_alt_enter:
            effect_msg = result.on_alt_enter
        elif action_id == "__launch__" and isinstance(result, ExtensionLaunchTrigger):
            self._active_ext = extension_registry.get(result.ext_id)
            launch_event: ipc.LaunchTriggerEvent = {
                "type": EventType.LAUNCH_TRIGGER,
                "args": (result.trigger_id,),
            }
            self._send_request(launch_event, callback)
            return
        else:
            activation_event: ipc.ResultActivationEvent = {
                "type": EventType.RESULT_ACTIVATION,
                "args": (action_id, result["__result_id__"]),
            }
            self._send_request(activation_event, callback)
            return

        if isinstance(effect_msg, dict) and effect_msg["type"] == EffectType.LEGACY_ACTIVATE_CUSTOM:
            custom_event: ipc.LegacyActivateCustomEvent = {
                "type": EventType.LEGACY_ACTIVATE_CUSTOM,
                "ref": effect_msg["ref"],
                "keep_app_open": effect_msg["keep_app_open"],
            }
            self._send_request(custom_event, callback)
            return

        callback(effect_msg)

    def _send_request(self, event: ipc.Request, callback: Callable[[EffectMessage], None]) -> None:
        """
        Send an event to the extension, expecting a response (passed to the callback).
        A request_id is sent alongside the event, used to filter out stale responses.

        For one-off messages, use ext.send_message() directly instead.
        """
        if not self._active_ext:
            logger.error("No active extension to send request to")
            return

        if not self._active_ext.owns_runtime:
            logger.warning("Cannot send event to inactive extension %s", self._active_ext.id)
            return

        self._request_id += 1
        self._pending_callback = callback
        self._active_ext.send_message(event, self._request_id)

    @events.on
    def handle_message(self, ext_id: str, message: ipc.ExtensionMessage) -> None:
        logger.debug("Incoming message %s from %r", summarize_ipc_args([message]), ext_id)
        if message["name"] == "response":
            if not self._active_ext:
                logger.error("No active extension to handle response")
                return
            if type(message.get("request_id")) is not int or not effect_utils.is_effect_message(
                message.get("response", {}).get("effect")
            ):
                logger.warning("Received malformed 'response' message from %s: %s", ext_id, message)
                return
            if self._active_ext.id != ext_id or not self._pending_callback or message["request_id"] != self._request_id:
                logger.debug("Ignoring outdated extension response")
                return
            response = message["response"]
            response["effect"] = self._rehydrate_results(self._active_ext, response["effect"])
            self._handle_response(response)
        elif message["name"] == "clipboard_store":
            if "text" not in message:
                logger.warning("Received malformed 'clipboard_store' message from %s: %s", ext_id, message)
                return
            # Extension API: only copies; the launcher stays open and the extension is
            # responsible for any subsequent UI changes.
            events.emit("app:clipboard_store", message["text"])
        elif message["name"] == "notify":
            if "body" not in message or "notification_id" not in message:
                logger.warning("Received malformed 'notify' message from %s: %s", ext_id, message)
                return
            ext = extension_registry.get(ext_id)
            if not ext:
                logger.warning("Notification sent from an extension, '%s', which was not found", ext_id)
                return
            events.emit(
                "app:show_notification",
                f"ext-{ext.id}-{message['notification_id']}",
                f"Message from {ext.manifest.name} extension",
                message["body"],
            )
        else:
            logger.warning("Received unknown message from %s: %s", ext_id, message)

    def _handle_response(self, response: ipc.Response) -> None:
        if not self._pending_callback:
            logger.debug("Ignoring outdated extension response")
            return

        effect_msg = response["effect"]

        if effect_msg["type"] != EffectType.RENDER_RESULTS and not response.get("keep_app_open", True):
            effect_utils.handle(effect_msg, prevent_close=True)
            effect_msg = effects.close_window()

        self._pending_callback(effect_msg)
        # A streamed render keeps the callback alive across batches; everything else is terminal.
        is_streaming_batch = effect_msg["type"] == EffectType.RENDER_RESULTS and not effect_msg.get("final", True)
        if not is_streaming_batch:
            self._pending_callback = None

    def _rehydrate_results(self, ext: ExtensionController, effect_msg: EffectMessage) -> EffectMessage:
        """Return the effect with raw result dicts in a RENDER_RESULTS effect replaced by Result objects.

        Reverses the dict-to-Result step that JSON serialization forced on the wire, resolving icons
        against the sending extension. Mutates and returns the same effect object rather than copying,
        since the caller has no use for the unrehydrated input.

        Recurses into LEGACY_RUN_MANY so results nested in a legacy ActionList are rehydrated too.
        """
        if effect_msg["type"] == EffectType.LEGACY_RUN_MANY:
            for nested_effect in effect_msg["effects"]:
                self._rehydrate_results(ext, nested_effect)
            return effect_msg
        if effect_msg["type"] != EffectType.RENDER_RESULTS:
            return effect_msg

        raw_results = effect_msg.get("results")
        rendered: list[Result] = []
        for index, result_dict in enumerate(raw_results):
            if not isinstance(result_dict, dict):
                logger.warning("Skipping malformed result from extension %s at index %s", ext.id, index)
                continue
            # The extension stamps each result with its cache id; carry it through so activation can
            # map back to the actual Result instance (see api.extension.Extension). A result without
            # one never entered that cache, so this positional fallback only keeps activation from
            # crashing; it cannot resolve to the original Result, and across a streamed request the
            # batch-local index may even repeat.
            result_dict.setdefault("__result_id__", index)
            try:
                result = Result(**result_dict)
            except (KeyError, TypeError, ValueError) as e:
                logger.warning("Skipping malformed result from extension %s at index %s: %s", ext.id, index, e)
                continue
            result.icon = ext.get_icon_value(result_dict.get("icon"))

            # Convert legacy actions to the new actions dictionary format
            if not result.actions:
                if result.on_enter:
                    result.actions["__legacy_on_enter__"] = {"name": "Main action"}
                if result.on_alt_enter:
                    result.actions["__legacy_on_alt_enter__"] = {"name": "Secondary action"}

            rendered.append(result)
        effect_msg["results"] = rendered
        return effect_msg
