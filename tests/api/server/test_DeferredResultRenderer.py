import mock
import pytest

from ulauncher.api.server.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.api.server.ExtensionController import ExtensionController
from ulauncher.api.server.ExtensionManifest import ExtensionManifest
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.event import BaseEvent, KeywordQueryEvent
from ulauncher.search.Query import Query


class TestDeferredResultRenderer:

    @pytest.fixture(autouse=True)
    def Timer(self, mocker):
        return mocker.patch('ulauncher.api.server.DeferredResultRenderer.Timer')

    @pytest.fixture(autouse=True)
    def GLib(self, mocker):
        return mocker.patch('ulauncher.api.server.DeferredResultRenderer.GLib')

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

    def test_handle_response__keep_app_open_is_False__hide_is_called(self, renderer, controller, GLib, mocker):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        response = mock.Mock()
        response.event = KeywordQueryEvent(Query('test'))
        response.action.keep_app_open.return_value = False
        renderer.active_event = response.event
        renderer.active_controller = controller
        renderer.handle_response(response, controller)
        GLib.idle_add.assert_called_with(UlauncherWindow.get_instance.return_value.hide_and_clear_input)

    def test_on_query_change__loading__is_canceled(self, renderer):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.on_query_change()
        timer.cancel.assert_called_once_with()
