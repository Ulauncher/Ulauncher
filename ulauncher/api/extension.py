from __future__ import annotations

import contextlib
import json
import logging
import os
import signal
import threading
from collections import defaultdict
from typing import Any, Callable, cast

from ulauncher.api.client.Client import Client
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import custom_data_store
from ulauncher.api.shared.event import BaseEvent, EventType, KeywordQueryEvent, PreferencesUpdateEvent, events
from ulauncher.internals.action_input import ActionMessageInput, convert_to_action_message
from ulauncher.internals.result import Result
from ulauncher.utils.logging_color_formatter import ColoredFormatter
from ulauncher.utils.timer import TimerContext, timer


class Extension:
    """
    Manages extension runtime.
    Used only within the extension process to handle events and communicate with Ulauncher.

    Create a subclass of this class and implement the methods you need.
    The methods are called when the corresponding event is triggered.
    """

    def __init__(self) -> None:
        self.ext_id = os.getenv("ULAUNCHER_EXTENSION_ID")
        assert self.ext_id, "ULAUNCHER_EXTENSION_ID env variable not set"
        self._input: str = ""
        self._client = Client(self)
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(ColoredFormatter())
        logging.basicConfig(level=logging.DEBUG if os.getenv("VERBOSE") else logging.WARNING, handlers=[log_handler])
        self.logger = logging.getLogger(self.ext_id)

        self._listeners: dict[Any, list[tuple[object, str | None]]] = defaultdict(list)
        self.preferences = {}
        self._input_debounce_timer: TimerContext | None = None
        self._input_debounce_delay = float(os.getenv("ULAUNCHER_INPUT_DEBOUNCE", "0.05"))
        self._result_cache: dict[int, Result] = {}
        signal.signal(signal.SIGTERM, lambda *_: self._client.unload())
        with contextlib.suppress(Exception):
            self.preferences = json.loads(os.environ.get("EXTENSION_PREFERENCES", "{}"))

        # subscribe with methods if user has added their own
        if self.__class__.on_input is not Extension.on_input:
            self.subscribe(events[EventType.INPUT_TRIGGER], "on_input")
        if self.__class__.on_launch is not Extension.on_launch:
            self.subscribe(events[EventType.LAUNCH_TRIGGER], "on_launch")
        if self.__class__.on_item_enter is not Extension.on_item_enter:
            self.subscribe(events[EventType.ACTIVATE_CUSTOM], "on_item_enter")
        if self.__class__.on_unload is not Extension.on_unload:
            self.subscribe(events[EventType.UNLOAD], "on_unload")
        if self.__class__.on_preferences_update is not Extension.on_preferences_update:
            self.subscribe(events[EventType.UPDATE_PREFERENCES], "on_preferences_update")
        if self.__class__.on_result_activation is not Extension.on_result_activation:
            self.subscribe(events[EventType.RESULT_ACTIVATION], "on_result_activation")

    def subscribe(self, event_type: type[BaseEvent], listener: str | object) -> None:
        """
        Example: extension.subscribe(InputTriggerEvent, "on_input")
        """
        method_name = None
        if isinstance(listener, str):
            method_name = listener
            listener = self

        self._listeners[event_type].append((listener, method_name))

    def convert_to_baseevent(self, event: dict[str, Any]) -> BaseEvent | None:
        event_type = event.get("type", "")
        args = event.get("args", [])
        event_constructor = events.get(event_type)
        # If pre v3 extension has KeywordQueryEvent, convert input_trigger to KeywordQueryEvent instead
        if event_type == EventType.INPUT_TRIGGER and self._listeners[KeywordQueryEvent]:
            argument, trigger_id = args
            return KeywordQueryEvent(f"{self.preferences[trigger_id]} {argument}")

        if event_type == EventType.ACTIVATE_CUSTOM:
            ref = event.get("ref", "")
            data = custom_data_store.get(ref)
            # Remove all entries except the one the user choose, because get_data can be called more than once
            custom_data_store.clear()
            custom_data_store[ref] = data
            args = [data]
        elif event_type == EventType.RESULT_ACTIVATION:
            # Restore actual Result instance from cache using the result_id
            action_id, result_dict = cast("tuple[str, dict[str, Any]]", args)
            result_id: int | None = result_dict.get("__result_id__")
            if result_id and (result := self._result_cache.get(result_id)):
                args = [action_id, result]
            else:
                err_msg = f"Result with id {result_id} not found"
                raise ValueError(err_msg)

        if callable(event_constructor):
            return event_constructor(args)

        return None

    def trigger_event(self, event: dict[str, Any]) -> None:
        """Trigger an event. If it's an input trigger it will be debounced"""
        if event.get("type") != EventType.INPUT_TRIGGER:
            self._do_trigger_event(event)
            return

        def trigger_debounced() -> None:
            self._input_debounce_timer = None
            self._do_trigger_event(event)

        if self._input_debounce_timer:
            self._input_debounce_timer.cancel()

        self._input_debounce_timer = timer(self._input_debounce_delay, trigger_debounced)

    def _do_trigger_event(self, event: dict[str, Any]) -> None:
        base_event = self.convert_to_baseevent(event)
        if not base_event:
            self.logger.warning("Dropping unknown event: %s", event)
            return

        event_type = type(base_event)
        listeners = self._listeners[event_type]

        # Ignore deprecated/useless PreferencesEvent event and optional UnloadEvent
        if not listeners and event_type.__name__ not in ["PreferencesEvent", "UnloadEvent"]:
            self.logger.debug("No listener for event %s", event_type.__name__)

        if event.get("type") == EventType.INPUT_TRIGGER:
            self._input = event.get("args", [])[0]

        for listener, method_name in listeners:
            method = getattr(listener, method_name or "on_event")
            # We can use method_name to determine if listener was added the old way or the new class method way
            # Pass the event args if method_name isn't None, otherwise event and self for backwards compatibility
            args = tuple(base_event.args) if method_name else (base_event, self)
            # Run in a separate thread to avoid blocking the message listener thread (client.py)
            threading.Thread(target=self.run_event_listener, args=(event, method, args)).start()

    def run_event_listener(
        self,
        event: dict[str, Any],
        method: Callable[..., ActionMessageInput | None],
        args: tuple[Any],
    ) -> None:
        current_input = self._input
        input_action_msg = method(*args)
        # ignore outdated responses
        if current_input == self._input:
            action_msg = convert_to_action_message(input_action_msg)

            # Cache Result objects before sending them, keyed by their Python object ID
            if isinstance(action_msg, list):
                self._result_cache.clear()
                for result in action_msg:
                    result_id = id(result)
                    self._result_cache[result_id] = result
                    # Add the result_id to the dict representation so Ulauncher can send it back
                    result["__result_id__"] = result_id

            self._client.send({"event": event, "action": action_msg})

    def run(self) -> None:
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        self.subscribe(events[EventType.UPDATE_PREFERENCES], PreferencesUpdateEventListener())
        self._client.connect()

    def on_input(self, query_str: str, trigger_id: str) -> ActionMessageInput | None:
        pass

    def on_launch(self, trigger_id: str) -> None:
        pass

    def on_item_enter(self, data: Any) -> ActionMessageInput | None:
        pass

    def on_preferences_update(self, pref_id: str, value: str | int | bool, previous_value: str | int | bool) -> None:
        pass

    def on_result_activation(self, action_id: str, result: Result) -> ActionMessageInput | None:
        """
        Called when user activates a result action.

        :param action_id: The ID of the action that was activated (key from Result.actions dict)
        :param result: The Result object that was activated
        :return: The action to execute
        """

    def on_unload(self) -> None:
        pass


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event: PreferencesUpdateEvent, extension: Extension) -> None:  # type: ignore[override]
        extension.preferences[event.id] = event.new_value
