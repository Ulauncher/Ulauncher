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

        assert GLib.idle_add.call_count == 2
        calls = GLib.idle_add.call_args_list
        expected_first_call_args = (UlauncherWindow.show_results, result_list)
        assert calls[0] == mock.call(*expected_first_call_args)

        expected_second_call_args = (UlauncherWindow.set_info, None, None)
        assert calls[1] == mock.call(*expected_second_call_args)
