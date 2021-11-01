import logging
from ulauncher.utils.decorator.debounce import debounce
from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.server.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.api.server.ExtensionPreferences import ExtensionPreferences
from ulauncher.api.server.ExtensionManifest import ExtensionManifest, ExtensionManifestError

logger = logging.getLogger(__name__)


class ExtensionController:
    """
    Handles communication between Ulauncher app and an extension.

    :param list controllers: list of :class:`~ulauncher.api.server.ExtensionController`
    """

    extension_id = None
    manifest = None
    preferences = None
    _debounced_send_event = None

    def __init__(self, controllers, framer, extension_id):
        self.controllers = controllers
        self.framer = framer
        self.result_renderer = DeferredResultRenderer.get_instance()  # type: DeferredResultRenderer
        self.configure(extension_id)
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
        event = KeywordQueryEvent(query)
        return self.trigger_event(event)

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

    def get_manifest(self):
        return self.manifest

    def get_extension_id(self):
        return self.extension_id

    # pylint: disable=unused-argument
    def handle_response(self, framer, response):
        """
        :meth:`~ulauncher.api.server.DeferredResultRenderer.DeferredResultRenderer.handle_response`
        of `DeferredResultRenderer`
        """
        if not isinstance(response, Response):
            raise Exception("Unsupported type %s" % type(response).__name__)

        logger.debug('Incoming response (%s, %s) from "%s"', type(response.event).__name__,
                     type(response.action).__name__,
                     self.extension_id)
        self.result_renderer.handle_response(response, self)

    def configure(self, extension_id):
        """
        * Adds itself to the controllers dict
        * Validates manifest file.
        * Sends :class:`PreferencesEvent` to extension
        """
        self.extension_id = extension_id
        if not self.extension_id:
            raise RuntimeError("No extension_id provided")

        logger.info('Extension "%s" connected', self.extension_id)

        self.manifest = ExtensionManifest.open(self.extension_id)
        try:
            self.manifest.validate()
        except ExtensionManifestError as e:
            logger.warning("Couldn't connect '%s'. %s: %s", self.extension_id, type(e).__name__, e)
            self.framer.close()
            return

        self.preferences = ExtensionPreferences.create_instance(self.extension_id)
        self.controllers[self.extension_id] = self
        self._debounced_send_event = debounce(self.manifest.get_option('query_debounce', 0.05))(self._send_event)

        self._send_event(PreferencesEvent(self.preferences.get_dict()))

    # pylint: disable=unused-argument
    def handle_close(self, framer):
        logger.info('Extension "%s" disconnected', self.extension_id)
        try:
            del self.controllers[self.extension_id]
        # pylint: disable=broad-except
        except Exception:
            pass
