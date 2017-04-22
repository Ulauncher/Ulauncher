import mock
import pytest
from ulauncher.search.Query import Query
from ulauncher.api.server.ExtensionSearchMode import ExtensionSearchMode
from ulauncher.api.server.ExtensionController import ExtensionController


class TestExtensionSearchMode:

    @pytest.fixture(autouse=True)
    def extServer(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionSearchMode.ExtensionServer.get_instance').return_value

    @pytest.fixture(autouse=True)
    def resultRenderer(self, mocker):
        return mocker.patch(
            'ulauncher.api.server.ExtensionSearchMode.DeferredResultRenderer.get_instance').return_value

    def test_is_enabled__controller_is_running__returns_true(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionSearchMode()
        query = Query('kw something')

        assert mode.is_enabled(query), 'Mode is not enabled'

    def xtest_is_enabled__query_only_contains_keyword__returns_false(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionSearchMode()
        query = Query('kw')

        assert not mode.is_enabled(query), 'Mode is enabled'

    def test_is_enabled__keyword__is_used_to_get_controller(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionSearchMode()
        query = Query('kw something')
        mode.is_enabled(query)

        extServer.get_controller_by_keyword.assert_called_with('kw')

    def test_handle_query__controller_handle_query__is_called(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionSearchMode()
        query = mock.create_autospec(Query)
        mode.handle_query(query)

        extServer.get_controller_by_keyword.return_value.handle_query.assert_called_with(query)

    def test_handle_query__controller_handle_query__is_returned(self, extServer):
        controller = mock.create_autospec(ExtensionController)
        extServer.get_controller_by_keyword.return_value = controller
        mode = ExtensionSearchMode()
        query = mock.create_autospec(Query)
        assert mode.handle_query(query) is extServer.get_controller_by_keyword.return_value.handle_query.return_value
