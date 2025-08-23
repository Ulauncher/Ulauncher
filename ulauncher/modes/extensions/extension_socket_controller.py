from __future__ import annotations

import contextlib
import logging
from typing import Any

from ulauncher.internals.query import Query
from ulauncher.modes.extensions import extension_finder
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
        self.ext_controller = ExtensionController.create(ext_id)
        ext_path = extension_finder.locate(ext_id)
        assert ext_path, f"No extension could be found matching {ext_id}"

        self.socket_controllers[ext_id] = self
        self._debounced_send_event = debounce(self.ext_controller.manifest.input_debounce)(self._send_event)

        # legacy_preferences_load is useless and deprecated
        prefs = {p_id: pref.value for p_id, pref in self.ext_controller.user_preferences.items()}
        self._send_event({"type": "event:legacy_preferences_load", "args": [prefs]})
        logger.info('Extension "%s" connected', ext_id)
        self.framer.connect("message_parsed", self.handle_response)
        self.framer.connect("closed", self.handle_close)

    def _send_event(self, event: dict[str, Any]) -> None:
        logger.debug('Send event %s to "%s"', type(event).__name__, self.ext_id)
        self.framer.send(event)

    def handle_query(self, query: Query) -> bool:
        """
        Handles user query with a keyword from this extension
        :returns: action object
        """
        triggers = self.ext_controller.user_triggers
        trigger_id = next((t_id for t_id, t in triggers.items() if t.user_keyword == query.keyword), None)

        return self.trigger_event(
            {
                "type": "event:input_trigger",
                "ext_id": self.ext_id,
                "args": [query.argument, trigger_id],
            }
        )

    def trigger_event(self, event: dict[str, Any]) -> bool:
        """
        Triggers event for an extension
        """
        # don't debounce events that are triggered by updates in preferences
        if event.get("type") == "event:update_preferences":
            self._send_event(event)
        else:
            self._debounced_send_event(event)

        events.emit("extension:handle_event", event, self)
        return True

    def handle_response(self, _framer: JSONFramer, response: dict[str, Any]) -> None:
        logger.debug(
            'Incoming response with keys "%s" from "%s"',
            set(response),
            self.ext_id,
        )
        events.emit("extension:handle_response", response, self)

    def handle_close(self, _framer: JSONFramer) -> None:
        logger.info('Extension "%s" disconnected', self.ext_id)
        with contextlib.suppress(Exception):
            del self.socket_controllers[self.ext_id]
