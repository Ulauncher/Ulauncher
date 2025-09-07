from typing import Any
from unittest.mock import MagicMock, create_autospec

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.modes.extensions.extension_mode import ExtensionMode
from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController
from ulauncher.modes.extensions.extension_socket_server import events as ess_events


class TestExtensionMode:
    @pytest.fixture(autouse=True)
    def ext_server(self, mocker: MockerFixture) -> Any:
        ess = mocker.patch("ulauncher.modes.extensions.extension_mode.ExtensionSocketServer").return_value
        ess_events.set_self(ess)
        return ess

    def test_is_enabled__query_only_contains_keyword__returns_false(self, ext_server: MagicMock) -> None:
        controller = create_autospec(ExtensionSocketController)
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()

        assert not mode.matches_query_str("kw"), "Mode is enabled"

    def test_handle_query__controller_handle_query__is_called(self, ext_server: MagicMock) -> None:
        controller = create_autospec(ExtensionSocketController)
        controller.ext_id = "com.example.asdf.ghjk"
        ext_server.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("asdf", "ghjk")
        mode.handle_query(query)

        ext_server.get_controller_by_keyword.return_value.handle_query.assert_called_with(query)
