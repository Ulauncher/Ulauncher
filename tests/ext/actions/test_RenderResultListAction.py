import mock
import pytest
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction


class TestRenderResultListAction:

    @pytest.fixture
    def result_list(self):
        return mock.Mock()

    @pytest.fixture
    def action(self, result_list):
        return RenderResultListAction(result_list)

    def test_keep_app_open(self, action):
        assert action.keep_app_open()

    def test_run(self, action, mocker, result_list):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        action.run()
        UlauncherWindow.get_instance.return_value.show_results.assert_called_with(result_list)
