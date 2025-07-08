from unittest import mock

import pytest

from ulauncher.internals.query import Query
from ulauncher.modes.extensions.extension_mode import ExtensionMode
from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController
from ulauncher.modes.extensions.extension_socket_server import events as ess_events


class TestExtensionMode:
    @pytest.fixture(autouse=True)
    def ext_server(self, mocker):
        ess = mocker.patch("ulauncher.modes.extensions.extension_mode.ExtensionSocketServer").return_value
        ess_events.set_self(ess)
        return ess

    def test_is_enabled__controller_is_running__returns_true(self, ext_server) -> None:
        controller = mock.create_autospec(ExtensionSocketController)
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        assert mode.parse_query_str("kw something"), "Mode is not enabled"

    def test_is_enabled__query_only_contains_keyword__returns_false(self, ext_server) -> None:
        controller = mock.create_autospec(ExtensionSocketController)
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()

        assert not mode.parse_query_str("kw"), "Mode is enabled"

    def test_is_enabled__keyword__is_used_to_get_controller(self, ext_server) -> None:
        controller = mock.create_autospec(ExtensionSocketController)
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        mode.parse_query_str("kw something")

        ext_server.get_controller_by_keyword.assert_called_with("kw")

    def test_handle_query__controller_handle_query__is_called(self, ext_server) -> None:
        controller = mock.create_autospec(ExtensionSocketController)
        controller.ext_id = "com.example.asdf.ghjk"
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("asdf", "ghjk")
        mode.handle_query(query)

        ext_server.get_controller_by_keyword.return_value.handle_query.assert_called_with(query)

    def test_handle_query__controller_handle_query__is_returned(self, ext_server) -> None:
        controller = mock.create_autospec(ExtensionSocketController)
        controller.ext_id = "com.example.asdf.ghjk"
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("asdf", "ghjk")
        assert mode.handle_query(query) is ext_server.get_controller_by_keyword.return_value.handle_query.return_value
