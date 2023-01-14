from unittest import mock
import pytest

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction


class TestRenderResultListAction:
    @pytest.fixture(autouse=True)
    def UlauncherApp(self, mocker):
        app = mocker.patch("ulauncher.ui.UlauncherApp.UlauncherApp")
        app.window = mocker.patch("ulauncher.ui.windows.UlauncherWindow.UlauncherWindow")()
        return app

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

    def test_run(self, action, result_list, GLib, UlauncherApp):
        action.run()
        GLib.idle_add.assert_called_with(UlauncherApp.get_instance.return_value.window.show_results, result_list)
