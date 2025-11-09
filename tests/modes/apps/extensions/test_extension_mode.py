from typing import Any
from unittest.mock import MagicMock, create_autospec

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.modes.extensions.extension_mode import ExtensionMode
from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController
from ulauncher.modes.extensions.extension_socket_server import events as ess_events
from ulauncher.utils import singleton


class TestExtensionMode:
    @pytest.fixture(autouse=True)
    def reset_singleton(self) -> None:
        # Reset singleton before each test
        singleton._instances.pop(ExtensionMode, None)

    @pytest.fixture(autouse=True)
    def ext_registry(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_mode.extension_registry")

    @pytest.fixture(autouse=True)
    def ext_server(self, mocker: MockerFixture) -> Any:
        ess = mocker.patch("ulauncher.modes.extensions.extension_mode.ExtensionSocketServer").return_value
        ess_events.set_self(ess)
        return ess

    def test_is_enabled__query_only_contains_keyword__returns_false(self, ext_server: MagicMock) -> None:
        keyword = "kw"
        controller = create_autospec(ExtensionSocketController)
        ext_server.socket_controllers.get.return_value = controller
        mode = ExtensionMode()
        mode._trigger_cache = {keyword: ("trigger_id", "ext_id")}

        assert not mode.matches_query_str(keyword), "Mode is enabled"

    def test_handle_query__controller_handle_query__is_called(self, ext_server: MagicMock) -> None:
        keyword = "asdf"
        ext_id = "com.test.ext"
        trigger_id = "trigger_id"
        mode = ExtensionMode()
        mode._trigger_cache = {keyword: (trigger_id, ext_id)}
        query = Query(keyword, "ghjk")
        mode.handle_query(query)
        ext_server.handle_query.assert_called_with(ext_id, trigger_id, query)

    def test_get_triggers__skips_extensions_not_running(self, ext_registry: MagicMock) -> None:
        trigger = MagicMock(keyword="kw", name="Trigger", description="Desc", icon="icon.png")
        ext = MagicMock()
        ext.is_enabled = True
        ext.has_error = False
        ext.is_running = False
        ext.id = "com.test.ext"
        ext.triggers = {"trigger-id": trigger}
        ext_registry.iterate.return_value = [ext]

        mode = ExtensionMode()

        assert list(mode.get_triggers()) == []
        assert mode._trigger_cache == {}
