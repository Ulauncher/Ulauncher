import logging
import pickle

from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.util.SimpleWebSocketServer import WebSocket
from ulauncher.util.decorator.debounce import debounce
from .DeferredResultRenderer import DeferredResultRenderer
from .ExtensionPreferences import ExtensionPreferences
from .ExtensionManifest import ExtensionManifest, ManifestValidationError

logger = logging.getLogger(__name__)


class ExtensionController(WebSocket):
    """
    Handles communication between Ulauncher app and an extension.

    :param list controllers: list of :class:`~ulauncher.api.server.ExtensionController`
    """

    extension_id = None
    manifest = None
    preferences = None
    _debounced_send_event = None

    def __init__(self, controllers, *args, **kw):
        self.controllers = controllers
        self.resultRenderer = DeferredResultRenderer.get_instance()
        super(ExtensionController, self).__init__(*args, **kw)

    def _send_event(self, event):
        logger.debug('Send event %s to "%s"' % (type(event).__name__, self.extension_id))
        self.sendMessage(pickle.dumps(event))

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
        if type(event) in [PreferencesUpdateEvent]:
            self._send_event(event)
        else:
            self._debounced_send_event(event)
        return self.resultRenderer.handle_event(event, self)

    def get_manifest(self):
        return self.manifest

    def get_extension_id(self):
        return self.extension_id

    def handleMessage(self):
        """
        Implements abstract method of :class:`WebSocket`

        Handles incoming message stored in `self.data` by invoking
        :meth:`~ulauncher.api.server.DeferredResultRenderer.DeferredResultRenderer.handle_response`
        of `DeferredResultRenderer`
        """
        response = pickle.loads(self.data)

        if not isinstance(response, Response):
            raise Exception("Unsupported type %s" % type(response).__name__)

        logger.debug('Incoming response (%s, %s) from "%s"' %
                     (type(response.event).__name__,
                      type(response.action).__name__,
                      self.extension_id))
        self.resultRenderer.handle_response(response, self)

    def handleConnected(self):
        """
        Implements abstract method of :class:`WebSocket`

        * Appends `self` to `self.controllers`
        * Validates manifest file.
        * Sends :class:`PreferencesEvent` to extension
        """
        self.extension_id = self.request.path[1:]
        if not self.extension_id:
            raise Exception('Incorrect path %s' % self.request.path)

        logger.info('Extension "%s" connected' % self.extension_id)

        self.manifest = ExtensionManifest.open(self.extension_id)
        try:
            self.manifest.validate()
        except ManifestValidationError as e:
            logger.warning("Couldn't connect '%s'. %s: %s" % (self.extension_id, type(e).__name__, e.message))
            self.close()
            return

        self.preferences = ExtensionPreferences.create_instance(self.extension_id)
        self.controllers[self.extension_id] = self
        self._debounced_send_event = debounce(self.manifest.get_option('query_debounce', 0.05))(self._send_event)

        self._send_event(PreferencesEvent(self.preferences.get_dict()))

    def handleClose(self):
        """
        Implements abstract method of :class:`WebSocket`
        """
        logger.info('Extension "%s" disconnected' % self.extension_id)
        try:
            del self.controllers[self.extension_id]
        except Exception:
            pass
