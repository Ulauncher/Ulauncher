from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController

TEST_EXT_ID = "com.example.test-ext-id"


class TestExtensionSocketController:
    @pytest.fixture
    def controllers(self) -> dict[str, ExtensionSocketController]:
        return {}

    @pytest.fixture(autouse=True)
    def extension_finder_locate(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_finder.locate")

    @pytest.fixture(autouse=True)
    def extension_registry(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.extensions.extension_socket_controller.extension_registry")

    @pytest.fixture
    def controller(self, controllers: dict[str, ExtensionSocketController]) -> ExtensionSocketController:
        controller = ExtensionSocketController(controllers, Mock(), TEST_EXT_ID)
        controller._debounced_send_event = controller.send_message
        return controller

    def test_configure__typical(
        self, controller: ExtensionSocketController, controllers: dict[str, ExtensionSocketController]
    ) -> None:
        # configure() is called implicitly when constructing the controller.
        assert controller.ext_id == TEST_EXT_ID
        assert controllers[TEST_EXT_ID] == controller
        framer: Any = controller.framer
        framer.send.assert_called_with({"type": "event:legacy_preferences_load", "args": [{}]})

    def test_trigger_event__send__is_called(self, controller: Any) -> None:
        event: Any = {}
        controller.trigger_event(event)
        controller.framer.send.assert_called_with(event)

    def test_handle_response__unsupported_data_type__exception_raised(self, controller: Any) -> None:
        controller.data = {}
        with pytest.raises(TypeError):
            controller.handle_response(controller.framer, object())
