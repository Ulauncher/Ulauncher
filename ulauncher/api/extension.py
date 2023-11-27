from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import threading
from collections import defaultdict
from typing import Any, Iterator

from ulauncher.api.client.Client import Client
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import custom_data_store
from ulauncher.api.shared.event import BaseEvent, KeywordQueryEvent, events
from ulauncher.utils.logging_color_formatter import ColoredFormatter


class Extension:
    """
    Manages extension runtime
    """

    def __init__(self):
        logHandler = logging.StreamHandler()
        logHandler.setFormatter(ColoredFormatter())
        logging.basicConfig(level=logging.DEBUG if os.getenv("VERBOSE") else logging.WARNING, handlers=[logHandler])
        self.extension_id = os.path.basename(os.path.dirname(sys.argv[0]))
        self.logger = logging.getLogger(self.extension_id)
        self._listeners = defaultdict(list)
        self._client = Client(self)
        self.preferences = {}
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

    def subscribe(self, event_type: type[BaseEvent], listener: str | object):
        """
        Example: extension.subscribe(InputTriggerEvent, "on_input")
        """
        method_name = None
        if isinstance(listener, str):
            method_name = listener
            listener = self

        self._listeners[event_type].append((listener, method_name))

    def convert_to_baseevent(self, event: dict) -> BaseEvent | None:
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

    def trigger_event(self, event: dict[str, Any]):
        base_event = self.convert_to_baseevent(event)
        if not base_event:
            self.logger.warning("Dropping unknown event: %s", event)
            return

        event_type = type(base_event)
        listeners = self._listeners[event_type]

        if not listeners:
            self.logger.debug("No listeners for event %s", event_type.__name__)

        for listener, method_name in listeners:
            method = getattr(listener, method_name or "on_event")
            # We can use method_name to determine if listener was added the old way or the new class method way
            # Pass the event args if method_name isn't None, otherwise event and self for backwards compatibility
            args = tuple(base_event.args) if method_name else (base_event, self)
            threading.Thread(target=self.run_event_listener, args=(event, method, args)).start()

    def run_event_listener(self, event, method, args):
        action = method(*args)
        if action is not None:
            # convert iterables to list
            if isinstance(action, Iterator):
                action = list(action)
            self._client.send({"event": event, "action": action})

    def run(self):
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        self.subscribe(events["event:update_preferences"], PreferencesUpdateEventListener())
        self._client.connect()

    def on_input(self, query: str, trigger_id: str):
        pass

    def on_launch(self, trigger_id: str):
        pass

    def on_item_enter(self, data):
        pass

    def on_preferences_update(self, id, value, previous_value):
        pass

    def on_unload(self):
        pass


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value
