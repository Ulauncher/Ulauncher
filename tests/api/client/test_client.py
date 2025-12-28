import os
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from pytest_mock import MockerFixture

from ulauncher.api.client.Client import Client
from ulauncher.api.extension import Extension
from ulauncher.api.shared.event import EventType


class TestClient:
    @pytest.fixture(autouse=True)
    def message_socket(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.client.Client.SocketMsgController")

    @pytest.fixture
    def extension(self) -> Extension:
        ext: Extension = create_autospec(Extension)
        ext.exec_path = "com.example.test-extension"
        ext.ext_id = "com.example.test-extension"
        return ext

    @pytest.fixture
    def client(self, extension: Any) -> Client:
        with patch.dict(os.environ, {"SOCKETPAIR_FD": "5"}):
            return Client(extension)

    def test_on_message__trigger_event__is_called(self, client: Client, extension: MagicMock) -> None:
        client.on_message({"hello": "world"})
        extension.trigger_event.assert_called_with({"hello": "world"})

    def test_unload(self, client: Client, extension: MagicMock) -> None:
        client.mainloop = MagicMock()
        client.mainloop.is_running.return_value = True
        client.unload()
        extension.trigger_event.assert_called_with({"type": EventType.UNLOAD})
        client.mainloop.quit.assert_called_once()
