from unittest import mock
import pytest

from ulauncher.api.client.Client import Client
from ulauncher.api.extension import Extension


class TestClient:
    @pytest.fixture(autouse=True)
    def UnloadEvent(self, mocker):
        return mocker.patch("ulauncher.api.client.Client.UnloadEvent")

    @pytest.fixture(autouse=True)
    def sock_client(self, mocker):
        return mocker.patch("ulauncher.api.client.Client.Gio.SocketClient")

    @pytest.fixture(autouse=True)
    def mainloop(self, mocker):
        return mocker.patch("ulauncher.api.client.Client.GLib.MainLoop.new")

    @pytest.fixture(autouse=True)
    def framer(self, mocker):
        return mocker.patch("ulauncher.api.client.Client.PickleFramer")

    @pytest.fixture(autouse=True)
    def timer(self, mocker):
        return mocker.patch("ulauncher.api.client.Client.timer")

    @pytest.fixture
    def extension(self):
        ext = mock.create_autospec(Extension)
        ext.extension_id = "com.example.test-extension"
        return ext

    @pytest.fixture
    def client(self, extension, framer, sock_client):
        client = Client(extension)
        client.framer = framer
        client.client = sock_client
        return client

    def test_connect__connect_is_called(self, client, mainloop):
        client.connect()
        client.client.connect.assert_called_once()
        client.framer.send.assert_called_once()
        mainloop.return_value.run.assert_called_once()

    def test_on_message__trigger_event__is_called(self, client, extension):
        client.on_message(mock.Mock(), {"hello": "world"})
        extension.trigger_event.assert_called_with({"hello": "world"})

    def test_on_close__UnloadEvent__is_triggered(self, client, extension, UnloadEvent):
        client.on_close(mock.Mock())
        extension.trigger_event.assert_called_with(UnloadEvent.return_value)

    def test_send__ws_send__is_called(self, client):
        client.send({"hello": "world"})
        client.framer.send.assert_called_with({"hello": "world"})
