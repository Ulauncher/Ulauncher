from unittest import mock
import pytest
from ulauncher.api.extension import Extension
from ulauncher.api.shared.action.BaseAction import BaseAction


class TestExtension:
    @pytest.fixture(autouse=True)
    def client(self, mocker):
        return mocker.patch("ulauncher.api.extension.Client").return_value

    @pytest.fixture(autouse=True)
    def response(self, mocker):
        return mocker.patch("ulauncher.api.extension.Response").return_value

    @pytest.fixture
    def extension(self):
        return Extension()

    @pytest.fixture
    def listener(self):
        return mock.Mock()

    def test_trigger_event__on_event__is_called(self, extension, listener):
        event = mock.Mock()
        extension.subscribe(type(event), listener)
        listener.on_event.return_value = mock.create_autospec(BaseAction)
        extension.trigger_event(event)
        listener.on_event.assert_called_with(event, extension)

    def test_trigger_event__action__is_sent(self, extension, listener, client, response):
        event = mock.Mock()
        listener.on_event.return_value = mock.create_autospec(BaseAction)
        extension.subscribe(type(event), listener)
        extension.trigger_event(event)
        client.send.assert_called_with(response)
