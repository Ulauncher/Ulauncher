from unittest import mock

import pytest

from ulauncher.modes.extensions.extension_socket_controller import ExtensionSocketController

TEST_EXT_ID = "com.example.test-ext-id"


class TestExtensionSocketController:
    @pytest.fixture
    def controllers(self):
        return {}

    @pytest.fixture(autouse=True)
    def ec_extension_finder(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.extension_controller.extension_finder")

    @pytest.fixture(autouse=True)
    def esc_extension_finder(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.extension_socket_controller.extension_finder")

    @pytest.fixture(autouse=True)
    def manifest(self, mocker):
        return mocker.patch(
            "ulauncher.modes.extensions.extension_socket_controller.ExtensionManifest.load"
        ).return_value

    @pytest.fixture
    def controller(self, controllers):
        controller = ExtensionSocketController(controllers, mock.Mock(), TEST_EXT_ID)
        controller._debounced_send_event = controller._send_event
        return controller

    def test_configure__typical(self, controller, controllers) -> None:
        # configure() is called implicitly when constructing the controller.
        assert controller.ext_id == TEST_EXT_ID
        assert controllers[TEST_EXT_ID] == controller
        controller.framer.send.assert_called_with({"type": "event:legacy_preferences_load", "args": [{}]})

    def test_trigger_event__send__is_called(self, controller) -> None:
        event = {}
        controller.trigger_event(event)
        controller.framer.send.assert_called_with(event)

    def test_handle_response__unsupported_data_type__exception_raised(self, controller) -> None:
        controller.data = {}
        with pytest.raises(TypeError):
            controller.handle_response(controller.framer, object())
