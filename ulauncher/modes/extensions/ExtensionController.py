from __future__ import annotations

import contextlib
import logging
import os
from typing import Any

from ulauncher.config import PATHS
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionManifestError
from ulauncher.utils.decorator.debounce import debounce

logger = logging.getLogger()


class ExtensionController:
    """
    Handles communication between Ulauncher app and an extension.

    :param list controllers: list of :class:`~ulauncher.modes.extensions.ExtensionController`
    """

    extension_id = None
    manifest: ExtensionManifest

    def __init__(self, controllers, framer, extension_id):
        if not extension_id:
            msg = "No extension_id provided"
            raise RuntimeError(msg)
        self.controllers = controllers
        self.framer = framer
        self.result_renderer = DeferredResultRenderer.get_instance()
        self.extension_id = extension_id
        self.manifest = ExtensionManifest.load_from_extension_id(extension_id)
        try:
            self.manifest.validate()
        except ExtensionManifestError as e:
            logger.warning("Couldn't connect '%s'. %s: %s", extension_id, type(e).__name__, e)
            self.framer.close()
            return

        self.controllers[extension_id] = self
        self._debounced_send_event = debounce(self.manifest.input_debounce)(self._send_event)

        # legacy_preferences_load is useless and deprecated
        self._send_event({"type": "event:legacy_preferences_load", "args": [self.manifest.get_user_preferences()]})
        logger.info('Extension "%s" connected', extension_id)
        self.framer.connect("message_parsed", self.handle_response)
        self.framer.connect("closed", self.handle_close)

    def _send_event(self, event):
        logger.debug('Send event %s to "%s"', type(event).__name__, self.extension_id)
        self.framer.send(event)

    def handle_query(self, query):
        """
        Handles user query with a keyword from this extension
        :returns: action object
        """
        trigger_id = self.manifest.find_matching_trigger(user_keyword=query.keyword)
        return self.trigger_event(
            {
                "type": "event:input_trigger",
                "ext_id": self.extension_id,
                "args": [query.argument, trigger_id],
            }
        )

    def trigger_event(self, event: dict[str, Any]):
        """
        Triggers event for an extension
        """
        # don't debounce events that are triggered by updates in preferences
        if event.get("type") == "event:update_preferences":
            self._send_event(event)
        else:
            self._debounced_send_event(event)
        return self.result_renderer.handle_event(event, self)

    def get_normalized_icon_path(self, icon=None) -> str:
        if not icon:
            icon = self.manifest.icon
        expanded_path = icon and f"{PATHS.EXTENSIONS}/{self.extension_id}/{icon}"
        return expanded_path if os.path.isfile(expanded_path) else icon

    def handle_response(self, _framer, response: dict[str, Any]):
        logger.debug(
            'Incoming response with keys "%s" from "%s"',
            set(response),
            self.extension_id,
        )
        self.result_renderer.handle_response(response, self)

    def handle_close(self, _framer):
        logger.info('Extension "%s" disconnected', self.extension_id)
        with contextlib.suppress(Exception):
            del self.controllers[self.extension_id]
