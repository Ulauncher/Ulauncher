import mock
import pytest
from ulauncher.result_list.item_action.BaseAction import BaseAction
from ulauncher.search.Query import Query
from ulauncher.extension.shared.event import KeywordQueryEvent, BaseEvent
from ulauncher.extension.server.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.extension.server.ExtensionManifest import ExtensionManifest
from ulauncher.extension.server.ExtensionController import ExtensionController


class TestDeferredResultRenderer:

    @pytest.fixture(autouse=True)
    def Timer(self, mocker):
        return mocker.patch('ulauncher.extension.server.DeferredResultRenderer.Timer')

    @pytest.fixture
    def event(self):
        return mock.create_autospec(BaseEvent)

    @pytest.fixture
    def manifest(self):
        return mock.create_autospec(ExtensionManifest)

    @pytest.fixture
    def controller(self, manifest):
        controller = mock.create_autospec(ExtensionController)
        controller.get_manifest.return_value = manifest
        return controller

    @pytest.fixture
    def renderer(self):
        return DeferredResultRenderer()

    def test_handle_event__result__instanceof_BaseAction(self, renderer, event, controller):
        result = renderer.handle_event(event, controller)
        assert isinstance(result, BaseAction)

    def test_handle_event__loading_timer__is_canceled(self, renderer, event, controller):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.handle_event(event, controller)
        timer.cancel.assert_called_once_with()

    def test_handle_response__action__is_ran(self, renderer, controller):
        response = mock.Mock()
        response.event = KeywordQueryEvent(Query('test'))
        renderer.active_event = response.event
        renderer.active_controller = controller
        renderer.handle_response(response, controller)
        response.action.run.assert_called_once_with()

    def test_on_query_change__loading__is_canceled(self, renderer):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.on_query_change()
        timer.cancel.assert_called_once_with()
