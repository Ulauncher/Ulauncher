from unittest import mock
import pytest

from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import InputTriggerEvent
from ulauncher.api.shared.query import Query


TEST_EXT_ID = "com.example.test-ext-id"


class TestExtensionController:
    @pytest.fixture
    def controllers(self):
        return {}

    @pytest.fixture(autouse=True)
    def PreferencesEvent(self, mocker):
        PreferencesEvent = mocker.patch("ulauncher.modes.extensions.ExtensionController.PreferencesEvent")
        PreferencesEvent.return_value = object()
        return PreferencesEvent

    @pytest.fixture(autouse=True)
    def result_renderer(self, mocker):
        return mocker.patch(
            "ulauncher.modes.extensions.ExtensionController.DeferredResultRenderer.get_instance"
        ).return_value

    @pytest.fixture(autouse=True)
    def manifest(self, mocker):
        return mocker.patch(
            "ulauncher.modes.extensions.ExtensionController.ExtensionManifest.load_from_extension_id"
        ).return_value

    @pytest.fixture
    def controller(self, controllers, mocker):
        controller = ExtensionController(controllers, mock.Mock(), TEST_EXT_ID)
        controller._debounced_send_event = controller._send_event
        return controller

    def test_configure__typical(self, controller, controllers, manifest, PreferencesEvent):
        # configure() is called implicitly when constructing the controller.
        manifest.get_user_preferences.return_value = {}
        assert controller.extension_id == TEST_EXT_ID
        assert controllers[TEST_EXT_ID] == controller
        controller.manifest.validate.assert_called_once()
        controller.framer.send.assert_called_with(PreferencesEvent.return_value)

    def test_trigger_event__send__is_called(self, controller):
        event = object()
        controller.trigger_event(event)
        controller.framer.send.assert_called_with(event)

    def test_handle_query__KeywordQueryEvent__is_sent_with_query(self, controller, result_renderer):
        query = Query("def ulauncher")
        assert controller.handle_query(query) == result_renderer.handle_event.return_value
        keywordEvent = controller.framer.send.call_args_list[1][0][0]
        assert isinstance(keywordEvent, InputTriggerEvent)
        assert keywordEvent.args[0] == "ulauncher"
        result_renderer.handle_event.assert_called_with(keywordEvent, controller)

    def test_handle_response__unsupported_data_type__exception_raised(self, controller):
        controller.data = dict()
        with pytest.raises(Exception):
            controller.handle_response(controller.framer, object())

    def test_handle_response__is_called(self, controller, result_renderer, mocker):
        response = Response(mock.Mock(), TestAction())

        controller.handle_response(controller.framer, response)

        result_renderer.handle_response.assert_called_with(response, controller)


class TestAction(BaseAction):
    pass
