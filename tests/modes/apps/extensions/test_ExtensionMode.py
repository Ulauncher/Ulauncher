from unittest import mock
import pytest
from ulauncher.modes.Query import Query
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.extensions.ExtensionController import ExtensionController


class TestExtensionMode:
    @pytest.fixture(autouse=True)
    def resultRenderer(self, mocker):
        return mocker.patch(
            'ulauncher.modes.extensions.ExtensionMode.DeferredResultRenderer.get_instance').return_value

    def test_is_enabled__controller_is_running__returns_true(self):
        controller = mock.create_autospec(ExtensionController)
        controller.extension_id = "test_id"
        mode = ExtensionMode()
        mode.keywords = {"kw": "test_id"}
        query = Query('kw something')

        assert mode.is_enabled(query), 'Mode is not enabled'

    def test_is_enabled__query_only_contains_keyword__returns_false(self):
        mode = ExtensionMode()
        query = Query('kw')

        assert not mode.is_enabled(query), 'Mode is enabled'
