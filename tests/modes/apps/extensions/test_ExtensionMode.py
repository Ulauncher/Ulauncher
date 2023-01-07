from unittest import mock
import pytest
from ulauncher.api.shared.query import Query
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.extensions.ExtensionController import ExtensionController


class TestExtensionMode:
    @pytest.fixture(autouse=True)
    def extServer(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionMode.ExtensionServer.get_instance").return_value

    @pytest.fixture(autouse=True)
    def resultRenderer(self, mocker):
        return mocker.patch("ulauncher.modes.extensions.ExtensionMode.DeferredResultRenderer.get_instance").return_value

    def test_is_enabled__controller_is_running__returns_true(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("kw something")

        assert mode.is_enabled(query), "Mode is not enabled"

    def xtest_is_enabled__query_only_contains_keyword__returns_false(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("kw")

        assert not mode.is_enabled(query), "Mode is enabled"

    def test_is_enabled__keyword__is_used_to_get_controller(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = Query("kw something")
        mode.is_enabled(query)

        extServer.get_controller_by_keyword.assert_called_with("kw")

    def test_handle_query__controller_handle_query__is_called(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = mock.create_autospec(Query)
        mode.handle_query(query)

        extServer.get_controller_by_keyword.return_value.handle_query.assert_called_with(query)

    def test_handle_query__controller_handle_query__is_returned(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionMode()
        query = mock.create_autospec(Query)
        assert mode.handle_query(query) is extServer.get_controller_by_keyword.return_value.handle_query.return_value
