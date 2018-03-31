import logging
from functools import partial
from port_finder import find_unused_port
from ulauncher.api.server.ExtensionController import ExtensionController
from ulauncher.util.SimpleWebSocketServer import SimpleWebSocketServer
from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton

logger = logging.getLogger(__name__)


class ExtensionServer(object):

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

    def __init__(self):
        self.hostname = '127.0.0.1'
        self.port = None
        self.ws_server = None
        self.controllers = {}

    def generate_ws_url(self, extension_id):
        """
        Returns WebSocket URL for given `extension_id`

        :rtype: str
        """
        if not self.is_running():
            raise ServerIsNotRunningError()

        return 'ws://%s:%s/%s' % (self.hostname, self.port, extension_id)

    def start(self):
        """
        Starts WS server
        """
        if self.ws_server:
            raise ServerIsRunningError()

        self._start_thread()

    @run_async(daemon=True)
    def _start_thread(self):
        self.port = self.port or find_unused_port(5054)
        logger.info('Starting WS server on port %s' % self.port)
        self.ws_server = SimpleWebSocketServer(self.hostname,
                                               self.port,
                                               partial(ExtensionController, self.controllers))
        self.ws_server.serveforever()
        self.ws_server = None
        logger.warning('WS server exited')

    def stop(self):
        """
        Stops WS server
        """
        if not self.is_running():
            raise ServerIsNotRunningError()

        self.ws_server.close()

    def is_running(self):
        """
        :rtype: bool
        """
        return bool(self.ws_server)

    def get_controller(self, extension_id):
        """
        :param str extension_id:
        :rtype: ~ulauncher.api.server.ExtensionController.ExtensionController
        """
        return self.controllers[extension_id]

    def get_controllers(self):
        """
        :rtype: list of  :class:`~ulauncher.api.server.ExtensionController.ExtensionController`
        """
        return self.controllers.values()

    def get_controller_by_keyword(self, keyword):
        """
        :param str keyword:
        :rtype: ~ulauncher.api.server.ExtensionController.ExtensionController
        """
        for ext_id, ctl in self.controllers.items():
            if keyword in ctl.preferences.get_active_keywords():
                return ctl


class ServerIsRunningError(RuntimeError):
    pass


class ServerIsNotRunningError(RuntimeError):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    server = ExtensionServer.get_instance()
    server.start()
