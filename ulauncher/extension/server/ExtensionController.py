import logging
import pickle
from ulauncher.utils.SimpleWebSocketServer import WebSocket
from ulauncher.utils.debounce import debounce
from ulauncher.extension.shared.event import KeywordQueryEvent, PreferencesEvent
from ulauncher.extension.shared.Response import Response
from ulauncher.result_list.item_action.BaseAction import BaseAction
from .DeferredResultRenderer import DeferredResultRenderer
from .ExtensionPreferences import ExtensionPreferences
from .ExtensionManifest import ExtensionManifest, ManifestValidationError

logger = logging.getLogger(__name__)


class ExtensionController(WebSocket):

    extension_id = None
    manifest = None
    preferences = None
    debounced_send_event = None

    def __init__(self, controllers, *args, **kw):
        self.controllers = controllers
        self.resultRenderer = DeferredResultRenderer.get_instance()
        super(ExtensionController, self).__init__(*args, **kw)

    def send_event(self, event):
        logger.debug('%s => "%s"' % (type(event).__name__, self.extension_id))
        self.sendMessage(pickle.dumps(event))

    def on_query_change(self, query):
        pass

    def handle_query(self, query):
        """
        Returns Action object
        """
        event = KeywordQueryEvent(query)
        self.debounced_send_event(event)

        return self.resultRenderer.handle_event(event, self)

    def get_manifest(self):
        return self.manifest

    def get_extension_id(self):
        return self.extension_id

    def handleMessage(self):
        """
        Inbound response
        """
        response = pickle.loads(self.data)

        if not isinstance(response, Response):
            raise Exception("Unsupported type %s" % type(response).__name__)

        logger.debug('%s <= "%s"' % (type(response.event).__name__, self.extension_id))
        self.resultRenderer.handle_response(response, self)

    def handleConnected(self):
        self.extension_id = self.request.path[1:]
        if not self.extension_id:
            raise Exception('Incorrect path %s' % self.request.path)

        logger.info('Extension "%s" connected' % self.extension_id)

        self.manifest = ExtensionManifest.open(self.extension_id)
        try:
            self.manifest.validate()
        except ManifestValidationError as e:
            logger.error("Couldn't connect '%s'. %s: %s" % (self.extension_id, type(e).__name__, e.message))
            self.close()
            return

        self.preferences = ExtensionPreferences(self.extension_id, self.manifest)
        self.controllers[self.extension_id] = self
        self.debounced_send_event = debounce(self.manifest.get_option('query_debounce', 0.05))(self.send_event)

        self.send_event(PreferencesEvent(self.preferences.get_dict()))

    def handleClose(self):
        logger.info('Extension "%s" disconnected' % self.extension_id)
        try:
            del self.controllers[self.extension_id]
        except Exception:
            pass
