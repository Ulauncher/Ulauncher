from __future__ import annotations

import contextlib
import logging
from typing import Any

from ulauncher.internals.query import Query
from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.decorator.debounce import debounce
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.framer import JSONFramer

logger = logging.getLogger()
events = EventBus()


class ExtensionSocketController:
    """
    Handles communication between Ulauncher app and an extension.
    """

    ext_id: str
    ext_controller: ExtensionController
    socket_controllers: dict[str, ExtensionSocketController]

    def __init__(
        self, socket_controllers: dict[str, ExtensionSocketController], framer: JSONFramer, ext_id: str
    ) -> None:
        if not ext_id:
            msg = "No ext_id provided"
            raise RuntimeError(msg)
        self.socket_controllers = socket_controllers
        self.framer: JSONFramer = framer
        self.ext_id = ext_id
        self.ext_controller = extension_registry.get_or_raise(ext_id)

        self.socket_controllers[ext_id] = self
        self._debounced_send_event = debounce(self.ext_controller.manifest.input_debounce)(self.send_message)

        # legacy_preferences_load is useless and deprecated
        prefs = {p_id: pref.value for p_id, pref in self.ext_controller.preferences.items()}
        self.send_message({"type": "event:legacy_preferences_load", "args": [prefs]})
        logger.info('Extension "%s" connected', ext_id)
        self.framer.connect("message_parsed", self.handle_response)
        self.framer.connect("closed", self.handle_close)

    def send_message(self, event: dict[str, Any]) -> None:
        logger.debug('Send event %s to "%s"', type(event).__name__, self.ext_id)
        self.framer.send(event)

    def handle_query(self, trigger_id: str, query: Query) -> None:
        """
        Handles user query with a keyword from this extension
        :returns: action object
        """
        self.trigger_event(
            {
                "type": "event:input_trigger",
                "ext_id": self.ext_id,
                "args": [query.argument, trigger_id],
            }
        )

    def trigger_event(self, event: dict[str, Any]) -> None:
        """
        Triggers event for an extension
        """
        self._debounced_send_event(event)

    def handle_response(self, _framer: JSONFramer, response: dict[str, Any]) -> None:
        logger.debug(
            'Incoming response with keys "%s" from "%s"',
            set(response),
            self.ext_id,
        )
        events.emit("extensions:handle_response", self.ext_id, response)

    def handle_close(self, _framer: JSONFramer) -> None:
        logger.info('Extension "%s" disconnected', self.ext_id)
        with contextlib.suppress(Exception):
            del self.socket_controllers[self.ext_id]
