from typing import Any, cast
from unittest.mock import MagicMock, create_autospec

import pytest
from pytest_mock import MockerFixture

from ulauncher.api.client.Client import Client
from ulauncher.api.extension import Extension


class TestClient:
    @pytest.fixture(autouse=True)
    def timer(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("threading.Timer")

    @pytest.fixture
    def extension(self) -> Extension:
        ext: Extension = create_autospec(Extension)
        ext.ext_id = "com.example.test-extension"
        return ext

    @pytest.fixture
    def client(self, extension: Any) -> Client:
        return Client(extension, MagicMock(), MagicMock())

    def test_on_message__trigger_event__is_called(self, client: Client, extension: MagicMock) -> None:
        client.on_message({"hello": "world"})
        extension.trigger_event.assert_called_with({"hello": "world"})

    def test_graceful_unload(self, client: Client, extension: MagicMock, timer: MagicMock) -> None:
        client.graceful_unload()
        extension.trigger_event.assert_called_with({"type": "event:unload"})
        timer.assert_called_once()

    def test_send__is_handled(self, client: Client) -> None:
        client.send({"hello": "world"})
        stdout_mock = cast("MagicMock", client.output_stream)
        stdout_mock.write.assert_called_with('{"hello": "world"}\n')
        stdout_mock.flush.assert_called_once()
