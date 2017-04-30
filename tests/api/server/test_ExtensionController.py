import mock
import pytest
import pickle

from ulauncher.api.server.ExtensionController import ExtensionController
from ulauncher.api.shared.Response import Response
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.search.Query import Query


class TestExtensionController:

    @pytest.fixture
    def controllers(self):
        return {}

    @pytest.fixture(autouse=True)
    def resultRenderer(self, mocker):
        return mocker.patch(
            'ulauncher.api.server.ExtensionController.DeferredResultRenderer.get_instance').return_value

    @pytest.fixture(autouse=True)
    def extPrefs(self, mocker):
        return mocker.patch(
            'ulauncher.api.server.ExtensionController.ExtensionPreferences').return_value

    @pytest.fixture(autouse=True)
    def manifest(self, mocker):
        return mocker.patch(
            'ulauncher.api.server.ExtensionController.ExtensionManifest.open').return_value

    @pytest.fixture
    def controller(self, controllers, mocker):
        server, sock, address = (None, None, None)
        controller = ExtensionController(controllers, server, sock, address)
        controller._debounced_send_event = controller._send_event

        # patch WebSocket.sendMessage()
        mocker.patch.object(controller, 'sendMessage')

        return controller

    def test_handleConnected__extension_id__is_stored(self, controller, controllers, extPrefs):
        extPrefs.get_dict.return_value = {}
        controller.request = mock.Mock()
        controller.request.path = '/extension-name'
        controller.handleConnected()
        assert controllers['extension-name'] == controller

    def test_handleConnected__invalid_extension_id__raises(self, controller):
        controller.request = mock.Mock()
        controller.request.path = '/'
        with pytest.raises(Exception):
            controller.handleConnected()

    def test_handleConnected__preferences__sent_to_client(self, controller, extPrefs, mocker):
        extPrefs.get_dict.return_value = {}
        controller.request = mock.Mock()
        controller.request.path = '/extension-name'
        PreferencesEvent = mocker.patch(
            'ulauncher.api.server.ExtensionController.PreferencesEvent')
        PreferencesEvent.return_value = object()
        mocker.patch.object(controller, '_send_event')
        controller.handleConnected()
        controller._send_event.assert_called_with(PreferencesEvent.return_value)

    def test_trigger_event__sendMessage__is_called_with_pickled_event(self, controller):
        event = object()
        controller.trigger_event(event)
        controller.sendMessage.assert_called_with(pickle.dumps(event))

    def test_handle_query__KeywordQueryEvent__is_sent_with_query(self, controller):
        query = Query('def ulauncher')
        controller.handle_query(query)
        keywordEvent = pickle.loads(controller.sendMessage.call_args_list[0][0][0])
        assert type(keywordEvent) is KeywordQueryEvent
        assert keywordEvent.get_query() == 'def ulauncher'

    def test_handle_query__handle_query__is_called(self, controller, resultRenderer):
        query = Query('def ulauncher')
        controller.extension_id = 'test_extension'
        controller.manifest = mock.Mock()
        assert controller.handle_query(query) == resultRenderer.handle_event.return_value
        resultRenderer.handle_event.assert_called_with(mock.ANY, controller)

    def test_handleMessage__unsupported_data_type__exception_raised(self, controller):
        controller.data = dict()
        with pytest.raises(Exception):
            controller.handleMessage()

    def test_handleMessage__handle_response__is_called(self, controller, resultRenderer, mocker):
        action = TestAction()
        event = mock.Mock()
        controller.extension_id = 'test_extension'
        controller.data = pickle.dumps(action)
        loads = mocker.patch('ulauncher.api.server.ExtensionController.pickle.loads')
        loads.return_value = Response(event, action)

        controller.handleMessage()

        resultRenderer.handle_response.assert_called_with(loads.return_value, controller)


class TestAction(BaseAction):
    pass
