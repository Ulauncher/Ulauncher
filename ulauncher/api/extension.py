import os
import json
import logging
from collections import defaultdict
from inspect import signature

from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesUpdateEvent, UnloadEvent
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Client import Client
from ulauncher.api.client.setup_logging import setup_logging, get_extension_name


class Extension:
    """
    Manages extension runtime
    """

    def __init__(self):
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.extension_id = get_extension_name()
        self._listeners = defaultdict(list)
        self._client = Client(self)
        self.preferences = {}
        try:
            self.preferences = json.loads(os.environ.get("EXTENSION_PREFERENCES", "{}"))
        except Exception:
            pass

        if not self.preferences:
            self.logger.error("Could not load user preferences")

        # subscribe with methods if user has added their own
        if self.__class__.on_query_change is not Extension.on_query_change:
            self.subscribe(KeywordQueryEvent, self, 'on_query_change')
        if self.__class__.on_item_enter is not Extension.on_item_enter:
            self.subscribe(ItemEnterEvent, self, 'on_item_enter')
        if self.__class__.on_unload is not Extension.on_unload:
            self.subscribe(UnloadEvent, self, 'on_unload')
        if self.__class__.on_preferences_update is not Extension.on_preferences_update:
            self.subscribe(PreferencesUpdateEvent, self, 'on_preferences_update')

    def subscribe(self, event_type, event_listener, method='on_event'):
        """
        Example:

            extension.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

        :param type event_type:
        :param ~ulauncher.api.client.EventListener.EventListener event_listener:
        :param str method:
        """
        self._listeners[event_type].append((event_listener, method))

    def get_listeners_for_event(self, event):
        """
        :param ~ulauncher.api.shared.event.BaseEvent event:
        :rtype: ~ulauncher.api.client.EventListener.EventListener
        """
        return self._listeners[type(event)]

    def trigger_event(self, event):
        """
        :param ~ulauncher.api.shared.event.BaseEvent event:
        """
        listeners = self.get_listeners_for_event(event)
        if not listeners:
            self.logger.debug('No listeners for event %s', type(event).__name__)
            return

        for listener, method in listeners:
            _method = getattr(listener, method)
            param_count = len(signature(_method).parameters)
            # method can and likely will be a member on self for new extensions, in which case
            # it can access self. But for backward compatibility we need to pass self
            action = _method(event) if param_count == 1 else _method(event, self)
            if action:
                assert isinstance(action, (list, BaseAction)), "on_event must return list of Results or a BaseAction"
                self._client.send(Response(event, action))

    def run(self):
        """
        Subscribes to events and connects to Ulauncher socket server
        """
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self._client.connect()

    def on_query_change(self, event):
        pass

    def on_item_enter(self, event):
        pass

    def on_preferences_update(self, event):
        pass

    def on_unload(self, event):
        pass


# pylint: disable=too-few-public-methods
class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value
