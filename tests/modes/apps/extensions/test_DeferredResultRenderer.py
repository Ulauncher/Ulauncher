from unittest import mock

import pytest

from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.ui.UlauncherApp import UlauncherApp

app = UlauncherApp()


class TestDeferredResultRenderer:
    @pytest.fixture(autouse=True)
    def UlauncherWindow(self, mocker):
        app.window = mocker.patch("ulauncher.ui.windows.UlauncherWindow.UlauncherWindow").return_value
        return app.window

    @pytest.fixture
    def renderer(self):
        return DeferredResultRenderer()

    def test_on_query_change__loading__is_canceled(self, renderer):
        timer = mock.Mock()
        renderer.loading = timer
        renderer.on_query_change()
        timer.cancel.assert_called_once_with()
