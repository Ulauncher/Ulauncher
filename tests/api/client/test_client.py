from typing import Any
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from ulauncher.api.client.Client import Client
from ulauncher.api.extension import Extension


class TestClient:
    @pytest.fixture(autouse=True)
    def sock_client(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.client.Client.Gio.SocketClient")

    @pytest.fixture(autouse=True)
    def mainloop(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.client.Client.GLib.MainLoop.new")

    @pytest.fixture(autouse=True)
    def framer(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.client.Client.JSONFramer")

    @pytest.fixture(autouse=True)
    def timer(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.client.Client.timer")

    @pytest.fixture
    def extension(self) -> Extension:
        ext: Extension = create_autospec(Extension)
        ext.exec_path = "com.example.test-extension"
        ext.ext_id = "com.example.test-extension"
        return ext

    @pytest.fixture
    def client(self, extension: Any, framer: Any, sock_client: Any) -> Client:
        client = Client(extension)
        client.framer = framer
        client.client = sock_client
        return client

    def test_connect__connect_is_called(self, client: Any, mainloop: Any) -> None:
        client.connect()
        client.client.connect.assert_called_once()
        client.framer.send.assert_called_once()
        mainloop.return_value.run.assert_called_once()

    def test_on_message__trigger_event__is_called(self, client: Client, extension: MagicMock) -> None:
        client.on_message(Mock(), {"hello": "world"})
        extension.trigger_event.assert_called_with({"hello": "world"})

    def test_on_close__unload_event__is_triggered(self, client: Client, extension: MagicMock) -> None:
        client.on_close(Mock())
        extension.trigger_event.assert_called_with({"type": "event:unload"})

    def test_send__framer_send__is_called(self, client: Client, framer: MagicMock) -> None:
        client.send({"hello": "world"})
        framer.send.assert_called_with({"hello": "world"})
