from unittest import mock

import pytest

from ulauncher.modes.extensions.ExtensionServer import ExtensionServer, ServerIsRunningError


class TestExtensionServer:
    @pytest.fixture(autouse=True)
    def SocketService(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.Gio.SocketService")

    @pytest.fixture(autouse=True)
    def UnixSocketAddress(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.Gio.UnixSocketAddress")

    @pytest.fixture(autouse=True)
    def ExtensionController(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.ExtensionController")

    @pytest.fixture(autouse=True)
    def path_exists(self, mocker):
        exists = mocker.patch("ulauncher.modes.extensions.ExtensionServer.os.path.exists")
        exists.return_value = False
        return exists

    @pytest.fixture(autouse=True)
    def GObject(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.GObject")

    @pytest.fixture(autouse=True)
    def unlink(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.os.unlink")

    @pytest.fixture(autouse=True)
    def JSONFramer(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionServer.JSONFramer")

    @pytest.fixture
    def server(self):
        return ExtensionServer()

    def test_start(self, server):
        server.start()
        server.service.connect.assert_called_once()
        server.service.add_address.assert_called_once()

    def test_start__clean_socket(self, server, path_exists, unlink):
        path_exists.return_value = True
        server.start()
        unlink.assert_called_once()

    def test_start__server_is_running__exception_raised(self, server):
        server.start()
        with pytest.raises(ServerIsRunningError):
            server.start()

    def test_handle_incoming(self, server, JSONFramer):
        conn = mock.Mock()
        source = mock.Mock()
        server.start()
        server.handle_incoming(server.service, conn, source)
        assert id(JSONFramer.return_value) in server.pending
        JSONFramer.return_value.set_connection.assert_called_with(conn)

    def test_handle_registration(self, server, JSONFramer, GObject, ExtensionController):
        conn = mock.Mock()
        source = mock.Mock()
        server.start()
        server.handle_incoming(server.service, conn, source)
        extid = "id"
        event = {"type": "extension:socket_connected", "ext_id": extid}
        assert id(JSONFramer.return_value) in server.pending
        server.handle_registration(JSONFramer.return_value, event)
        assert id(JSONFramer.return_value) not in server.pending
        assert GObject.signal_handler_disconnect.call_count == 2
        ExtensionController.assert_called_once()

    def test_stop(self, server):
        server.start()
        assert server.is_running()
        service = server.service
        server.stop()
        assert not server.is_running()
        assert service.stop.call_count == 1
        assert service.close.call_count == 1
