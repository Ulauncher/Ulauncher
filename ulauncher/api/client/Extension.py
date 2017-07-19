import logging
from collections import defaultdict

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import PreferencesEvent, PreferencesUpdateEvent
from .Client import Client
from .setup_logging import setup_logging


class Extension(object):
    """
    Manages extension runtime
    """

    def __init__(self):
        self._listeners = defaultdict(list)
        self._client = Client(self)
        self.preferences = {}
        self.logger = logging.getLogger(__name__)
        setup_logging()

    def subscribe(self, event_type, event_listener):
        """
        Example:

            extension.subscribe(PreferencesEvent, PreferencesEventListener())

        :param type event_type:
        :param ~ulauncher.api.client.EventListener.EventListener event_listener:
        """
        self._listeners[event_type].append(event_listener)

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
            self.logger.debug('No listeners for event %s' % type(event).__name__)
            return

        for listener in listeners:
            action = listener.on_event(event, self)
            if action:
                assert isinstance(action, BaseAction), "on_event return value is not an instance of BaseAction"
                self._client.send(Response(event, action))

    def run(self):
        """
        Subscribes to events and connects to Ulauncher WS server
        """
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self._client.connect()


class PreferencesEventListener(EventListener):

    def on_event(self, event, extension):
        extension.preferences.update(event.preferences)


class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value
