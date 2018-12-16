from time import sleep

import mock
import pytest

from ulauncher.api.server.ExtensionServer import ExtensionServer, ServerIsRunningError


class TestExtensionServer:

    @pytest.fixture(autouse=True)
    def find_unused_port(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionServer.find_unused_port')

    @pytest.fixture(autouse=True)
    def SWS(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionServer.SimpleWebSocketServer')

    @pytest.fixture
    def server(self):
        return ExtensionServer()

    @pytest.fixture(autouse=True)
    def run_async(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionServer.run_async')

    def test_start__SimpleWebSocketServer__is_created(self, server, SWS, find_unused_port):
        server.start()
        sleep(0.02)
        SWS.assert_called_with('127.0.0.1', find_unused_port.return_value, mock.ANY)

    def test_start__serveforever__is_called(self, server, SWS):
        server.start()
        sleep(0.02)
        SWS.return_value.serveforever.assert_called_with()

    def test_start__server_is_running__exception_raised(self, server):
        server.ws_server = mock.Mock()
        with pytest.raises(ServerIsRunningError):
            server.start()

    def test_generate_ws_url(self, server):
        server.ws_server = mock.Mock()
        server.port = 3297
        assert server.generate_ws_url('test_extension') == 'ws://127.0.0.1:3297/test_extension'

    def test_stop__close__is_called(self, server):
        server.ws_server = mock.Mock()
        server.stop()
        server.ws_server.close.assert_called_with()

    def test_get_controller_by_keyword__keyword_found__controller_returned(self, server):
        controller = mock.Mock()
        controller.preferences.get_active_keywords.return_value = ['yt', 'af']
        server.controllers['test_extension'] = controller
        assert server.get_controller_by_keyword('yt') == controller

    def test_get_controller_by_keyword__keyword_not_found__None_returned(self, server):
        controller = mock.Mock()
        controller.preferences.get_active_keywords.return_value = ['yt', 'af']
        server.controllers['test_extension'] = controller
        assert server.get_controller_by_keyword('fw') is None
