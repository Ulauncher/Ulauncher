import os
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from pytest_mock import MockerFixture

from ulauncher.api.extension import Extension
from ulauncher.api.shared.event import EventType
from ulauncher.api.socket_client import Client


class TestClient:
    @pytest.fixture(autouse=True)
    def message_socket(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.api.socket_client.SocketMsgController")

    @pytest.fixture
    def extension(self) -> Extension:
        ext: Extension = create_autospec(Extension)
        ext.ext_id = "com.example.test-extension"
        return ext

    @pytest.fixture
    def client(self, extension: Any) -> Client:
        with patch.dict(os.environ, {"SOCKETPAIR_FD": "5"}):
            return Client(extension)

    def test_on_message__trigger_event__is_called(self, client: Client, extension: MagicMock) -> None:
        client.on_message(({"type": "event:input_trigger", "args": ("q", "t")}, 42))
        extension.trigger_event.assert_called_with({"type": "event:input_trigger", "args": ("q", "t")}, 42)

    def test_unload(self, client: Client, extension: MagicMock) -> None:
        client.mainloop = MagicMock()
        client.mainloop.is_running.return_value = True
        client.unload()
        extension.trigger_event.assert_called_with({"type": EventType.UNLOAD})
        client.mainloop.quit.assert_called_once()
