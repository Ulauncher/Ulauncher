import pickle
import mock
import pytest

from ulauncher.api.client.Client import Client
from ulauncher.api.client.Extension import Extension


class TestClient:

    @pytest.fixture(autouse=True)
    def SystemExitEvent(self, mocker):
        return mocker.patch('ulauncher.api.client.Client.SystemExitEvent')

    @pytest.fixture(autouse=True)
    def Timer(self, mocker):
        return mocker.patch('ulauncher.api.client.Client.Timer')

    @pytest.fixture(autouse=True)
    def websocket(self, mocker):
        return mocker.patch('ulauncher.api.client.Client.websocket')

    @pytest.fixture
    def extension(self):
        return mock.create_autospec(Extension)

    @pytest.fixture
    def client(self, extension):
        return Client(extension, ws_api_url="ws://localhost:5000/test_extension")

    def test_connect__WebSocketApp__is_called(self, client, websocket):
        client.connect()
        websocket.WebSocketApp.assert_called_with('ws://localhost:5000/test_extension',
                                                  on_message=mock.ANY,
                                                  on_error=mock.ANY,
                                                  on_open=mock.ANY,
                                                  on_close=mock.ANY)

    def test_connect__run_forever__is_called(self, client, websocket):
        client.connect()
        websocket.WebSocketApp.return_value.run_forever.assert_called_with()

    def test_on_message__trigger_event__is_called(self, client, extension):
        client.on_message(mock.Mock(), pickle.dumps({'hello': 'world'}))
        extension.trigger_event.assert_called_with({'hello': 'world'})

    def test_on_close__SystemExitEvent__is_triggered(self, client, extension, SystemExitEvent):
        client.on_close(mock.Mock())
        extension.trigger_event.assert_called_with(SystemExitEvent.return_value)

    def test_send__ws_send__is_called(self, client):
        client.ws = mock.Mock()
        client.send({'hello': 'world'})
        client.ws.send.assert_called_with(pickle.dumps({'hello': 'world'}))
