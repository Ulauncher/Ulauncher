from __future__ import annotations

import contextlib
import inspect
import json
import logging
import os
import signal
import threading
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, cast

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.api._logging import get_extension_logger
from ulauncher.api.event import BaseEvent, EventType, LegacyKeywordQueryEvent, PreferencesUpdateEvent, events
from ulauncher.api.socket_client import Client
from ulauncher.internals import effect_utils, effects, ipc
from ulauncher.internals.result import Result
from ulauncher.utils import scheduling

if TYPE_CHECKING:
    from ulauncher.api.client.EventListener import EventListener as LegacyEventListener


class Extension:
    """
    Manages extension runtime.
    Used only within the extension process to handle events and communicate with Ulauncher.

    Create a subclass of this class and implement the methods you need.
    The methods are called when the corresponding event is triggered.
    """

    def __init__(self) -> None:
        self.ext_id = os.getenv("ULAUNCHER_EXTENSION_ID")
        if not self.ext_id:
            err_msg = "ULAUNCHER_EXTENSION_ID env variable not set"
            raise RuntimeError(err_msg)
        self._client = Client(self)

        # Set up logging level for the root logger
        logging.basicConfig(
            level=logging.DEBUG if os.getenv("VERBOSE") == "1" else logging.WARNING,
        )

        self.logger = get_extension_logger()

        self._listeners: dict[type[BaseEvent], list[tuple[LegacyEventListener | Extension, str | None]]] = defaultdict(
            list
        )
        self.preferences = {}
        self._input_request_id: int = 0
        self._input_debounce_timer: scheduling.Context | None = None
        self._input_debounce_delay = float(os.getenv("ULAUNCHER_INPUT_DEBOUNCE", "0.05"))
        self._result_cache: dict[int, Result] = {}
        self._cache_request_id: int | None = None
        signal.signal(signal.SIGTERM, lambda *_: self._client.unload())
        with contextlib.suppress(Exception):
            # TODO: #1741 - migration path to remove trigger keywords from preferences
            self.preferences = json.loads(os.environ.get("EXTENSION_PREFERENCES", "{}"))

        # subscribe with methods if user has added their own
        if self.__class__.on_input is not Extension.on_input:
            self._subscribe(events[EventType.INPUT_TRIGGER], "on_input")
        if self.__class__.on_launch is not Extension.on_launch:
            self._subscribe(events[EventType.LAUNCH_TRIGGER], "on_launch")
        if self.__class__.on_item_enter is not Extension.on_item_enter:
            self._subscribe(events[EventType.LEGACY_ACTIVATE_CUSTOM], "on_item_enter")
        if self.__class__.on_unload is not Extension.on_unload:
            self._subscribe(events[EventType.UNLOAD], "on_unload")
        if self.__class__.on_preferences_update is not Extension.on_preferences_update:
            self._subscribe(events[EventType.UPDATE_PREFERENCES], "on_preferences_update")
        if self.__class__.on_result_activation is not Extension.on_result_activation:
            self._subscribe(events[EventType.RESULT_ACTIVATION], "on_result_activation")

    def subscribe(self, event_type: type[BaseEvent], listener: LegacyEventListener) -> None:
        """
        Example: extension.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        """
        warn_legacy_api(
            "Extension.subscribe",
            "Define handler methods like `on_input` on your `Extension` subclass instead.",
        )
        self._subscribe(event_type, listener)

    def _subscribe(self, event_type: type[BaseEvent], listener: str | LegacyEventListener) -> None:
        if isinstance(listener, str):
            self._listeners[event_type].append((self, listener))
        else:
            self._listeners[event_type].append((listener, None))

    def convert_to_baseevent(self, event: ipc.Event) -> BaseEvent | None:
        event_constructor = events.get(event["type"])
        if not callable(event_constructor):
            return None

        if event["type"] == EventType.LEGACY_ACTIVATE_CUSTOM:
            # Only reachable if the extension used the legacy ExtensionCustomAction, so import its store
            # lazily here to avoid loading the legacy module (and its deprecation warning) otherwise.
            from ulauncher.api.shared.action.ExtensionCustomAction import custom_data_store as legacy_custom_data_store

            data = legacy_custom_data_store.get(event["ref"])
            return event_constructor([data])

        if event["type"] == EventType.RESULT_ACTIVATION:
            # Restore actual Result instance from cache using the result_id
            action_id, result_id = event["args"]
            result = self._result_cache.get(result_id)
            if result is None:
                err_msg = f"Result with id {result_id} not found"
                raise ValueError(err_msg)
            return event_constructor([action_id, result])

        if event["type"] == EventType.UNLOAD:
            return event_constructor([])

        # If pre v3 extension has LegacyKeywordQueryEvent, convert input_trigger to LegacyKeywordQueryEvent instead
        if event["type"] == EventType.INPUT_TRIGGER and self._listeners[LegacyKeywordQueryEvent]:
            argument, trigger_id = event["args"]
            return LegacyKeywordQueryEvent(f"{self.preferences[trigger_id]} {argument}")

        return event_constructor(list(event["args"]))

    def trigger_event(self, event: ipc.Event, request_id: int | None = None) -> None:
        """Trigger an event. If it's an input trigger it will be debounced"""
        if event["type"] != EventType.INPUT_TRIGGER:
            self._do_trigger_event(event, request_id)
            return

        def trigger_debounced() -> None:
            self._input_debounce_timer = None
            self._do_trigger_event(event, request_id)

        if self._input_debounce_timer:
            self._input_debounce_timer.cancel()

        self._input_debounce_timer = scheduling.timer(self._input_debounce_delay, trigger_debounced)

    def _do_trigger_event(self, event: ipc.Event, request_id: int | None = None) -> None:
        base_event = self.convert_to_baseevent(event)
        if not base_event:
            self.logger.warning("Dropping unknown event: %s", event)
            return

        event_type = type(base_event)
        input_request_id: int | None = None
        listeners = self._listeners[event_type]

        if event["type"] == EventType.INPUT_TRIGGER:
            self._input_request_id += 1
            input_request_id = self._input_request_id

        # A new render replaces the old result list, so drop its custom-action data (dropping it on
        # activation instead would lose sibling actions still on screen under keep_app_open).
        if (
            event["type"] in (EventType.INPUT_TRIGGER, EventType.LAUNCH_TRIGGER)
            and self._listeners[events[EventType.LEGACY_ACTIVATE_CUSTOM]]
        ):
            from ulauncher.api.shared.action.ExtensionCustomAction import custom_data_store as legacy_custom_data_store

            legacy_custom_data_store.clear()

        # Keep preferences in sync before dispatching, so a user on_preferences_update handler reading
        # self.preferences sees the new value. Dispatch runs listeners in threads with no ordering guarantee.
        if isinstance(base_event, PreferencesUpdateEvent):
            self.preferences[base_event.id] = base_event.new_value

        # Ignore deprecated/useless LegacyPreferencesEvent and optional UnloadEvent
        if not listeners and event_type.__name__ not in ["LegacyPreferencesEvent", "UnloadEvent"]:
            self.logger.debug("No listener for event %s", event_type.__name__)
            if request_id is not None:
                # Requests need a response to be able to garbage collect their callbacks
                self._send_response(request_id, event, effects.do_nothing(), input_request_id)
            return

        for listener, method_name in listeners:
            method = getattr(listener, method_name or "on_event")
            # We can use method_name to determine if listener was added the old way or the new class method way
            # Pass the event args if method_name isn't None, otherwise event and self for backwards compatibility
            args = tuple(base_event.args) if method_name else (base_event, self)
            # Run in a separate thread to avoid blocking the message listener thread (socket_client.py)
            # It's not possible to cancel threads without process isolation, so we run multiple simultaneous threads,
            # then discard the result for stale events
            threading.Thread(
                target=self.run_event_listener, args=(request_id, event, method, args, input_request_id)
            ).start()

    def run_event_listener(
        self,
        request_id: int | None,
        event: ipc.Event,
        method: Callable[..., effects.EffectMessageInput | None],
        args: tuple[Any, ...],
        input_request_id: int | None = None,
    ) -> None:
        result = method(*args)
        if request_id is None:
            return

        # A generator streams its results in batches: `yield result` appends one, `yield [results]`
        # replaces the list. Anything else (a returned list, effect, bool, ...) is a single response.
        if inspect.isgenerator(result):
            self._stream_response(request_id, event, result, input_request_id)
        else:
            # Schedule the response on the main thread to avoid races on shared state
            effect_msg = effect_utils.convert_to_effect_message(result)
            if event["type"] == EventType.INPUT_TRIGGER and not effect_utils.is_valid_input_effect(effect_msg):
                self.logger.warning(
                    "Invalid effect %s from input handler. Supported types are: results, `effect.do_nothing()`,"
                    "legacy `DoNothingAction()` or a legacy `ActionList()` which doesn't close the window",
                    effect_msg["type"],
                )
                effect_msg = effects.do_nothing()
            scheduling.run_when_idle(self._send_response, request_id, event, effect_msg, input_request_id)

    def _stream_response(
        self,
        request_id: int,
        event: ipc.Event,
        generator: Iterator[Result | list[Result]],
        input_request_id: int | None,
    ) -> None:
        """Send one render batch per yielded item, then a final empty batch to close the stream.

        A yielded single result appends, while a yielded list replaces the rendered list.

        After the yield, an empty closing (final=True) batch is sent separately. If nothing was streamed,
        it clears any prior results (append=False).

        A superseding input stops the loop with no closing batch, since that input renders its own; an
        exception raised mid-stream propagates and likewise sends none. Ulauncher keeps the request's
        callback alive until a closing batch or the next input, so partial results stay on screen.
        """

        def emit(effect_msg: effects.RenderResults) -> None:
            # Schedule the response on the main thread to avoid races on shared state
            scheduling.run_when_idle(self._send_response, request_id, event, effect_msg, input_request_id, log=False)

        self.logger.debug("Streaming results for request %s", request_id)
        batches = 0
        for item in generator:
            if input_request_id is not None and input_request_id != self._input_request_id:
                self.logger.debug("Streaming for request %s superseded after %s batch(es)", request_id, batches)
                return
            append = not isinstance(item, list)
            results = [item] if append else list(item)
            emit(effects.render_results(results, append=append, final=False))
            batches += 1

        emit(effects.render_results([], append=bool(batches), final=True))
        self.logger.debug("Finished streaming %s result batch(es) for request %s", batches, request_id)

    def _send_response(
        self,
        request_id: int,
        event: ipc.Event,
        effect_msg: effects.EffectMessage,
        input_request_id: int | None,
        log: bool = True,
    ) -> bool:
        if input_request_id is not None and input_request_id != self._input_request_id:
            return False

        if effect_msg["type"] == effects.EffectType.RENDER_RESULTS:
            self._assign_result_ids(request_id, effect_msg)

        response: ipc.Response = {"effect": effect_msg}
        if event["type"] == EventType.LEGACY_ACTIVATE_CUSTOM:
            response["keep_app_open"] = event["keep_app_open"]
        self._client.send({"name": "response", "request_id": request_id, "response": response}, log=log)
        return False

    def _assign_result_ids(self, request_id: int, effect_msg: effects.RenderResults) -> None:
        """Give each result a stable id, cache it for activation lookup, and stamp the id onto a wire
        copy without mutating the result the extension handed us. Ids stay unique for the whole
        request; only a new request starts a fresh id space.
        """
        # A replace batch must not reuse ids: the previous batch can still be on screen (its paint is
        # throttled downstream), so an activation of a visible result would resolve to a new one.
        if request_id != self._cache_request_id:
            self._result_cache = {}
            self._cache_request_id = request_id
        wire_results: list[Result] = []
        for result in effect_msg["results"]:
            result_id = len(self._result_cache)
            self._result_cache[result_id] = result
            wire_results.append(cast("Result", {**result, "__result_id__": result_id}))
        effect_msg["results"] = wire_results

    def run(self) -> None:
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        # Trigger legacy preferences load event synthetically since the app no longer sends it
        self._do_trigger_event({"type": EventType.LEGACY_PREFERENCES_LOAD, "args": (self.preferences,)})
        self._client.connect()

    def clipboard_store(self, text: str) -> None:
        """Copy text to the clipboard."""
        if not isinstance(text, str):
            msg = f'Clipboard text "{text}" is invalid. It must be a string'
            raise TypeError(msg)

        self._client.send({"name": "clipboard_store", "text": text})

    def notify(self, body: str = "", notification_id: str | None = None) -> None:
        """
        Show a desktop notification.

        :param str body: Notification body text (optional)
        :param str | None notification_id: Optional ID for notification deduplication
        """
        if not isinstance(body, str):
            msg = f'Notification body "{body}" is invalid. It must be a string'
            raise TypeError(msg)
        if notification_id is not None and not isinstance(notification_id, str):
            msg = f'Notification ID "{notification_id}" is invalid. It must be a string or None'
            raise TypeError(msg)

        self._client.send({"name": "notify", "body": body, "notification_id": notification_id})

    def on_input(self, _query_str: str, _trigger_id: str) -> Iterable[Result | list[Result]]:
        # Return a list of results, or yield to stream them: `yield result` appends one,
        # `yield [results]` replaces the list (see _stream_response).
        return []

    def on_launch(self, trigger_id: str) -> None:
        pass

    def on_item_enter(self, data: Any) -> effects.EffectMessageInput | None:
        pass

    def on_preferences_update(self, pref_id: str, value: str | int | bool, previous_value: str | int | bool) -> None:
        pass

    def on_result_activation(self, action_id: str, result: Result) -> effects.EffectMessageInput | None:
        """
        Called when user activates a result action.

        :param action_id: The ID of the action that was activated (key from Result.actions dict)
        :param result: The Result object that was activated
        :return: The effect to execute
        """

    def on_unload(self) -> None:
        pass
