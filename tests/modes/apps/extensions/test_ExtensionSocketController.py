from unittest import mock

import pytest

from ulauncher.api.shared.query import Query
from ulauncher.modes.extensions.ExtensionSocketController import ExtensionSocketController

TEST_EXT_ID = "com.example.test-ext-id"
MOCK_SETTINGS = {"pref_id": "pref_val"}


class TestExtensionSocketController:
    @pytest.fixture
    def controllers(self):
        return {}

    @pytest.fixture(autouse=True)
    def result_renderer(self, mocker):
        return mocker.patch(
            "ulauncher.modes.extensions.ExtensionSocketController.DeferredResultRenderer.get_instance"
        ).return_value

    @pytest.fixture(autouse=True)
    def extension_finder(self, mocker):
        ef = mocker.patch("ulauncher.modes.extensions.ExtensionSocketController.extension_finder")
        ef.locate = lambda ext_id: f"./.tmp/ulauncher_tests/{ext_id}"
        return ef

    @pytest.fixture(autouse=True)
    def manifest(self, mocker):
        manifest = mocker.patch(
            "ulauncher.modes.extensions.ExtensionSocketController.ExtensionManifest.load"
        ).return_value
        manifest.get_key_value_user_preferences.return_value = MOCK_SETTINGS
        return manifest

    @pytest.fixture
    def controller(self, controllers):
        controller = ExtensionSocketController(controllers, mock.Mock(), TEST_EXT_ID)
        controller._debounced_send_event = controller._send_event
        return controller

    def test_configure__typical(self, controller, controllers, manifest):
        # configure() is called implicitly when constructing the controller.
        manifest.get_key_value_user_preferences.return_value = {}
        assert controller.ext_id == TEST_EXT_ID
        assert controllers[TEST_EXT_ID] == controller
        controller.framer.send.assert_called_with({"type": "event:legacy_preferences_load", "args": [MOCK_SETTINGS]})

    def test_trigger_event__send__is_called(self, controller):
        event = {}
        controller.trigger_event(event)
        controller.framer.send.assert_called_with(event)

    def test_handle_query__KeywordQueryEvent__is_sent_with_query(self, controller, result_renderer):
        query = Query("def ulauncher")
        assert controller.handle_query(query) == result_renderer.handle_event.return_value
        keywordEvent = controller.framer.send.call_args_list[1][0][0]
        assert keywordEvent.get("type") == "event:input_trigger"
        assert keywordEvent.get("args", [])[0] == "ulauncher"
        result_renderer.handle_event.assert_called_with(keywordEvent, controller)

    def test_handle_response__unsupported_data_type__exception_raised(self, controller):
        controller.data = {}
        with pytest.raises(TypeError):
            controller.handle_response(controller.framer, object())

    def test_handle_response__is_called(self, controller, result_renderer):
        response = {"event": mock.Mock(), "action": {}}

        controller.handle_response(controller.framer, response)

        result_renderer.handle_response.assert_called_with(response, controller)
