from __future__ import annotations

import contextlib
import logging
from typing import Any

from ulauncher.api.shared.query import Query
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest
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
    data_controller: ExtensionController
    manifest: ExtensionManifest

    def __init__(self, controllers: dict[str, ExtensionSocketController], framer: JSONFramer, ext_id: str) -> None:
        if not ext_id:
            msg = "No ext_id provided"
            raise RuntimeError(msg)
        self.controllers = controllers
        self.framer: JSONFramer = framer
        self.ext_id = ext_id
        self.data_controller = ExtensionController.create(ext_id)
        ext_path = extension_finder.locate(ext_id)
        assert ext_path, f"No extension could be found matching {ext_id}"
        self.manifest = ExtensionManifest.load(ext_path)

        self.controllers[ext_id] = self
        self._debounced_send_event = debounce(self.manifest.input_debounce)(self._send_event)

        # legacy_preferences_load is useless and deprecated
        prefs = {id: pref.value for id, pref in self.manifest.get_user_preferences(ext_id).items()}
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
        triggers = self.data_controller.user_triggers
        trigger_id = next((id for id, t in triggers.items() if t.user_keyword == query.keyword), None)

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
        action = response.get("action")
        if isinstance(action, list):
            for result in action:
                result["icon"] = self.data_controller.get_normalized_icon_path(result["icon"])

        events.emit("extension:handle_response", response, self)

    def handle_close(self, _framer: JSONFramer) -> None:
        logger.info('Extension "%s" disconnected', self.ext_id)
        with contextlib.suppress(Exception):
            del self.controllers[self.ext_id]
