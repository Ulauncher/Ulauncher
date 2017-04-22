import mock
import pytest

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction


class TestRenderResultListAction:

    @pytest.fixture(autouse=True)
    def GLib(self, mocker):
        return mocker.patch('ulauncher.api.shared.action.RenderResultListAction.GLib')

    @pytest.fixture
    def result_list(self):
        return mock.Mock()

    @pytest.fixture
    def action(self, result_list):
        return RenderResultListAction(result_list)

    def test_keep_app_open(self, action):
        assert action.keep_app_open()

    def test_run(self, action, mocker, result_list, GLib):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        action.run()
        GLib.idle_add.assert_called_with(UlauncherWindow.get_instance.return_value.show_results, result_list)
