from types import MethodType
from unittest import mock

import pytest

from ulauncher.api.shared.event import BaseEvent, KeywordQueryEvent
from ulauncher.api.shared.query import Query
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest
from ulauncher.ui.UlauncherApp import UlauncherApp


class TestDeferredResultRenderer:
    @pytest.fixture(autouse=True)
    def UlauncherWindow(self, mocker):
        app = UlauncherApp.get_instance()
        app.window = mocker.patch("ulauncher.ui.windows.UlauncherWindow.UlauncherWindow").return_value
        return app.window

    @pytest.fixture(autouse=True)
    def timer(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.DeferredResultRenderer.timer")

    @pytest.fixture
    def event(self):
        return mock.create_autospec(BaseEvent)

    @pytest.fixture
    def manifest(self):
        return mock.create_autospec(ExtensionManifest)

    @pytest.fixture
    def controller(self):
        ctrl = mock.create_autospec(ExtensionController)
        ctrl.get_normalized_icon_path = MethodType(lambda _: "/path/to/asdf.png", ctrl)
        return ctrl

    @pytest.fixture
    def renderer(self):
        return DeferredResultRenderer()

    def test_handle_event__loading_timer__is_canceled(self, renderer, event, controller):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.handle_event(event, controller)
        timer.cancel.assert_called_once_with()

    def test_handle_response__action__is_ran(self, renderer, controller):
        action = mock.Mock()
        event = KeywordQueryEvent(Query("test"))
        response = {"event": event, "action": action}
        renderer.active_event = event
        renderer.active_controller = controller
        renderer.handle_response(response, controller)

    def test_handle_response__keep_app_open_is_False__hide_is_called(self, renderer, controller):
        action = mock.Mock()
        action.keep_app_open = False
        event = KeywordQueryEvent(Query("test"))
        response = {"event": event, "action": action}
        renderer.active_event = event
        renderer.active_controller = controller
        renderer.handle_response(response, controller)

    def test_on_query_change__loading__is_canceled(self, renderer):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.on_query_change()
        timer.cancel.assert_called_once_with()
