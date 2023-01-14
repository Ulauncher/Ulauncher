import logging
import os
import os.path
from functools import lru_cache
from gi.repository import Gio, GObject

from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.api.shared.socket_path import get_socket_path
from ulauncher.api.shared.event import RegisterEvent
from ulauncher.utils.framer import PickleFramer

logger = logging.getLogger()


class ExtensionServer:
    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls):
        return cls()

    def __init__(self):
        self.service = None
        self.socket_path = get_socket_path()
        self.controllers = {}
        self.pending = {}

    def start(self):
        """
        Starts extension server
        """
        if self.is_running():
            raise ServerIsRunningError()

        self.service = Gio.SocketService.new()
        self.service.connect("incoming", self.handle_incoming)

        if os.path.exists(self.socket_path):
            logger.debug("Removing existing socket path %s", self.socket_path)
            os.unlink(self.socket_path)

        self.service.add_address(
            Gio.UnixSocketAddress.new(self.socket_path), Gio.SocketType.STREAM, Gio.SocketProtocol.DEFAULT, None
        )
        self.pending = {}
        self.controllers = {}

    # pylint: disable=unused-argument
    def handle_incoming(self, service, conn, source):
        framer = PickleFramer()
        msg_handler_id = framer.connect("message_parsed", self.handle_registration)
        closed_handler_id = framer.connect("closed", self.handle_pending_close)
        self.pending[id(framer)] = (framer, msg_handler_id, closed_handler_id)
        framer.set_connection(conn)

    def handle_pending_close(self, framer):
        self.pending.pop(id(framer))

    def handle_registration(self, framer, event):
        if isinstance(event, RegisterEvent):
            pended = self.pending.pop(id(framer))
            if pended:
                for msg_id in pended[1:]:
                    GObject.signal_handler_disconnect(framer, msg_id)
            ExtensionController(self.controllers, framer, event.extension_id)
        else:
            logger.debug("Unhandled message received: %s", event)

    def stop(self):
        """
        Stops extension server
        """
        if not self.is_running():
            raise ServerIsNotRunningError()

        self.service.stop()
        self.service.close()
        self.service = None

    def is_running(self):
        """
        :rtype: bool
        """
        return bool(self.service)

    def get_controllers(self):
        """
        :rtype: list of  :class:`~ulauncher.modes.extensions.ExtensionController.ExtensionController`
        """
        return self.controllers.values()

    def get_controller_by_keyword(self, keyword):
        """
        :param str keyword:
        :rtype: ~ulauncher.modes.extensions.ExtensionController.ExtensionController
        """
        for controller in self.controllers.values():
            for trigger in controller.manifest.triggers.values():
                if keyword and keyword == trigger.user_keyword:
                    return controller

        return None


class ServerIsRunningError(RuntimeError):
    pass


class ServerIsNotRunningError(RuntimeError):
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    server = ExtensionServer.get_instance()
    server.start()
