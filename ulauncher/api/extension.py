import sys
import os
import json
import logging
from typing import Iterator, Type, Union
from collections import defaultdict

from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import BaseEvent, KeywordQueryEvent, ItemEnterEvent, PreferencesUpdateEvent, UnloadEvent
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Client import Client
from ulauncher.api.client.setup_logging import setup_logging


class Extension:
    """
    Manages extension runtime
    """

    def __init__(self):
        setup_logging()
        self.extension_id = os.path.basename(os.path.dirname(sys.argv[0]))
        self.logger = logging.getLogger(self.extension_id)
        self._listeners = defaultdict(list)
        self._client = Client(self)
        self.preferences = {}
        try:
            self.preferences = json.loads(os.environ.get("EXTENSION_PREFERENCES", "{}"))
        except Exception:
            pass

        # subscribe with methods if user has added their own
        if self.__class__.on_query_change is not Extension.on_query_change:
            self.subscribe(KeywordQueryEvent, 'on_query_change')
        if self.__class__.on_item_enter is not Extension.on_item_enter:
            self.subscribe(ItemEnterEvent, 'on_item_enter')
        if self.__class__.on_unload is not Extension.on_unload:
            self.subscribe(UnloadEvent, 'on_unload')
        if self.__class__.on_preferences_update is not Extension.on_preferences_update:
            self.subscribe(PreferencesUpdateEvent, 'on_preferences_update')

    def subscribe(self, event_type: Type[BaseEvent], listener: Union[str, object]):
        """
        Example: extension.subscribe(KeywordQueryEvent, "on_query_change")
        """
        method_name = None
        if isinstance(listener, str):
            method_name = listener
            listener = self

        self._listeners[event_type].append((listener, method_name))

    def trigger_event(self, event: BaseEvent):
        event_type = type(event)
        listeners = self._listeners[event_type]
        if not listeners:
            self.logger.debug('No listeners for event %s', event_type.__name__)
            return

        for listener, method_name in listeners:
            method = getattr(listener, method_name or "on_event")
            # We can use method_name to determine if listener was added the old way or the new class method way
            # Pass the event args if method_name isn't None, otherwise event and self for backwards compatibility
            action = method(*event.args) if method_name else method(event, self)
            if action:
                if isinstance(action, Iterator):
                    action = list(action)
                assert isinstance(action, (list, BaseAction)), "on_event must return list of Results or a BaseAction"
                self._client.send(Response(event, action))

    def run(self):
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self._client.connect()

    def on_query_change(self, query):
        pass

    def on_item_enter(self, data):
        pass

    def on_preferences_update(self, id, value, previous_value):
        pass

    def on_unload(self):
        pass


# pylint: disable=too-few-public-methods
class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value
