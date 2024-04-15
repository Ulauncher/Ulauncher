from unittest import mock

import pytest

from ulauncher.modes.extensions.ExtensionSocketController import ExtensionSocketController

TEST_EXT_ID = "com.example.test-ext-id"


class TestExtensionSocketController:
    @pytest.fixture
    def controllers(self):
        return {}

    @pytest.fixture(autouse=True)
    def ec_extension_finder(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionController.extension_finder")

    @pytest.fixture(autouse=True)
    def esc_extension_finder(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionSocketController.extension_finder")

    @pytest.fixture(autouse=True)
    def manifest(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionSocketController.ExtensionManifest.load").return_value

    @pytest.fixture
    def controller(self, controllers):
        controller = ExtensionSocketController(controllers, mock.Mock(), TEST_EXT_ID)
        controller._debounced_send_event = controller._send_event
        return controller

    def test_configure__typical(self, controller, controllers):
        # configure() is called implicitly when constructing the controller.
        assert controller.ext_id == TEST_EXT_ID
        assert controllers[TEST_EXT_ID] == controller
        controller.framer.send.assert_called_with({"type": "event:legacy_preferences_load", "args": [{}]})

    def test_trigger_event__send__is_called(self, controller):
        event = {}
        controller.trigger_event(event)
        controller.framer.send.assert_called_with(event)

    def test_handle_response__unsupported_data_type__exception_raised(self, controller):
        controller.data = {}
        with pytest.raises(TypeError):
            controller.handle_response(controller.framer, object())
