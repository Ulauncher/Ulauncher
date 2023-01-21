from unittest import mock
import pytest
from ulauncher.ui.UlauncherApp import UlauncherApp
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction


class TestRenderResultListAction:
    @pytest.fixture(autouse=True)
    def UlauncherWindow(self, mocker):
        app = UlauncherApp.get_instance()
        app.window = mocker.patch("ulauncher.ui.windows.UlauncherWindow.UlauncherWindow").return_value
        return app.window

    @pytest.fixture(autouse=True)
    def GLib(self, mocker):
        return mocker.patch("ulauncher.api.shared.action.RenderResultListAction.GLib")

    @pytest.fixture
    def result_list(self):
        return mock.Mock()

    @pytest.fixture
    def action(self, result_list):
        return RenderResultListAction(result_list)

    def test_keep_app_open(self, action):
        assert action.keep_app_open

    def test_run(self, action, result_list, GLib, UlauncherWindow):
        action.run()
        GLib.idle_add.assert_called_with(UlauncherWindow.show_results, result_list)
