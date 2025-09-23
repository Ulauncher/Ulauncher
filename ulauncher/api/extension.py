from __future__ import annotations

import contextlib
import json
import logging
import os
import signal
import threading
from collections import defaultdict
from typing import Any, Callable, Iterator

from ulauncher.api.client.Client import Client
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import custom_data_store
from ulauncher.api.shared.event import BaseEvent, KeywordQueryEvent, PreferencesUpdateEvent, events
from ulauncher.internals.result import ActionMetadata
from ulauncher.utils.logging_color_formatter import ColoredFormatter
from ulauncher.utils.timer import TimerContext, timer

PLACEHOLDER_DELAY = 0.3  # delay in sec before Loading... is rendered


class Extension:
    _placeholder_result_timer: TimerContext | None = None
    """
    Manages extension runtime.
    Used only within the extension process to handle events and communicate with Ulauncher.

    Create a subclass of this class and implement the methods you need.
    The methods are called when the corresponding event is triggered.
    """

    def __init__(self) -> None:
        self._input: str = ""
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(ColoredFormatter())
        logging.basicConfig(level=logging.DEBUG if os.getenv("VERBOSE") else logging.WARNING, handlers=[log_handler])
        self.ext_id = os.getenv("ULAUNCHER_EXTENSION_ID")
        assert self.ext_id, "ULAUNCHER_EXTENSION_ID env variable not set"
        self.logger = logging.getLogger(self.ext_id)
        self._listeners: dict[Any, list[tuple[object, str | None]]] = defaultdict(list)
        self._client = Client(self)
        self.preferences = {}
        signal.signal(signal.SIGTERM, lambda signal, _frame: self._client.graceful_unload(signal))
        with contextlib.suppress(Exception):
            self.preferences = json.loads(os.environ.get("EXTENSION_PREFERENCES", "{}"))

        # subscribe with methods if user has added their own
        if self.__class__.on_input is not Extension.on_input:
            self.subscribe(events["event:input_trigger"], "on_input")
        if self.__class__.on_launch is not Extension.on_launch:
            self.subscribe(events["event:launch_trigger"], "on_launch")
        if self.__class__.on_item_enter is not Extension.on_item_enter:
            self.subscribe(events["event:activate_custom"], "on_item_enter")
        if self.__class__.on_unload is not Extension.on_unload:
            self.subscribe(events["event:unload"], "on_unload")
        if self.__class__.on_preferences_update is not Extension.on_preferences_update:
            self.subscribe(events["event:update_preferences"], "on_preferences_update")

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
        if event_type == "event:input_trigger" and self._listeners[KeywordQueryEvent]:
            argument, trigger_id = args
            return KeywordQueryEvent(f"{self.preferences[trigger_id]} {argument}")

        if event_type == "event:activate_custom":
            ref = event.get("ref", "")
            data = custom_data_store.get(ref)
            # Remove all entries except the one the user choose, because get_data can be called more than once
            custom_data_store.clear()
            custom_data_store[ref] = data
            args = [data]

        if callable(event_constructor):
            return event_constructor(args)

        return None

    def trigger_event(self, event: dict[str, Any]) -> None:
        base_event = self.convert_to_baseevent(event)
        if not base_event:
            self.logger.warning("Dropping unknown event: %s", event)
            return

        event_type = type(base_event)
        listeners = self._listeners[event_type]

        # Ignore deprecated/useless PreferencesEvent event and optional UnloadEvent
        if not listeners and event_type.__name__ not in ["PreferencesEvent", "UnloadEvent"]:
            self.logger.debug("No listener for event %s", event_type.__name__)

        if event.get("type") == "event:input_trigger":
            self._input = event.get("args", [])[0]

        for listener, method_name in listeners:
            method = getattr(listener, method_name or "on_event")
            # We can use method_name to determine if listener was added the old way or the new class method way
            # Pass the event args if method_name isn't None, otherwise event and self for backwards compatibility
            args = tuple(base_event.args) if method_name else (base_event, self)
            # Run in a separate thread to avoid blocking the message listener thread (client.py)
            threading.Thread(target=self.run_event_listener, args=(event, method, args)).start()

    def run_event_listener(
        self, event: dict[str, Any], method: Callable[..., ActionMetadata | None], args: tuple[Any]
    ) -> None:
        current_input = self._input
        self._clear_placeholder_timeout()
        self._placeholder_result_timer = timer(
            PLACEHOLDER_DELAY, lambda: self._client.send({"event": event, "action": [{"name": "Loading..."}]})
        )
        action_metadata = method(*args)

        # convert iterables to list
        if isinstance(action_metadata, Iterator):
            action_metadata = [*action_metadata]

        self._clear_placeholder_timeout()

        # ignore outdated responses
        if current_input == self._input and action_metadata is not None:
            self._client.send({"event": event, "action": action_metadata})

    def _clear_placeholder_timeout(self) -> None:
        if self._placeholder_result_timer:
            self._placeholder_result_timer.cancel()
            self._placeholder_result_timer = None

    def run(self) -> None:
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        self.subscribe(events["event:update_preferences"], PreferencesUpdateEventListener())
        self._client.connect()

    def on_input(self, query_str: str, trigger_id: str) -> None:
        pass

    def on_launch(self, trigger_id: str) -> None:
        pass

    def on_item_enter(self, data: Any) -> None:
        pass

    def on_preferences_update(self, pref_id: str, value: str | int | bool, previous_value: str | int | bool) -> None:
        pass

    def on_unload(self) -> None:
        pass


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event: PreferencesUpdateEvent, extension: Extension) -> None:  # type: ignore[override]
        extension.preferences[event.id] = event.new_value
