import os
import logging
from ulauncher.config import PATHS
from ulauncher.utils.decorator.debounce import debounce
from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.event import InputTriggerEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionManifestError

logger = logging.getLogger()


class ExtensionController:
    """
    Handles communication between Ulauncher app and an extension.

    :param list controllers: list of :class:`~ulauncher.modes.extensions.ExtensionController`
    """

    extension_id = None
    manifest: ExtensionManifest
    _debounced_send_event = None

    def __init__(self, controllers, framer, extension_id):
        if not extension_id:
            raise RuntimeError("No extension_id provided")
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
        # Use default if unspecified or 0.
        self._debounced_send_event = debounce(self.manifest.input_debounce or 0.05)(self._send_event)

        # PreferencesEvent is candidate for future removal
        self._send_event(PreferencesEvent(self.manifest.get_user_preferences()))
        logger.info('Extension "%s" connected', extension_id)
        self.framer.connect("message_parsed", self.handle_response)
        self.framer.connect("closed", self.handle_close)

    def _send_event(self, event):
        logger.debug('Send event %s to "%s"', type(event).__name__, self.extension_id)
        self.framer.send(event)

    def handle_query(self, query):
        """
        Handles user query with a keyword from this extension
        :returns: :class:`BaseAction` object
        """
        trigger_id = self.manifest.find_matching_trigger(user_keyword=query.keyword)
        return self.trigger_event(InputTriggerEvent(trigger_id, query.argument))

    def trigger_event(self, event):
        """
        Triggers event for an extension
        """
        # don't debounce events that are triggered by updates in preferences
        if isinstance(event, PreferencesUpdateEvent):
            self._send_event(event)
        else:
            self._debounced_send_event(event)
        return self.result_renderer.handle_event(event, self)

    def get_normalized_icon_path(self, icon=None) -> str:
        if not icon:
            icon = self.manifest.icon
        expanded_path = icon and f"{PATHS.EXTENSIONS}/{self.extension_id}/{icon}"
        return expanded_path if os.path.isfile(expanded_path) else icon

    # pylint: disable=unused-argument
    def handle_response(self, framer, response):
        """
        :meth:`~ulauncher.modes.extensions.DeferredResultRenderer.DeferredResultRenderer.handle_response`
        of `DeferredResultRenderer`
        """
        if not isinstance(response, Response):
            raise Exception(f"Unsupported type {type(response).__name__}")

        logger.debug(
            'Incoming response (%s, %s) from "%s"',
            type(response.event).__name__,
            type(response.action).__name__,
            self.extension_id,
        )
        self.result_renderer.handle_response(response, self)

    # pylint: disable=unused-argument
    def handle_close(self, framer):
        logger.info('Extension "%s" disconnected', self.extension_id)
        try:
            del self.controllers[self.extension_id]
        # pylint: disable=broad-except
        except Exception:
            pass
