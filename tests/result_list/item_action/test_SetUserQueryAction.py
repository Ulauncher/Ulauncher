import mock
import pytest
from time import sleep
from ulauncher.result_list.item_action.SetUserQueryAction import SetUserQueryAction


class TestSetUserQueryAction:

    @pytest.fixture
    def window(self, mocker):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        return UlauncherWindow.get_instance.return_value

    @pytest.fixture
    def action(self, window):
        return SetUserQueryAction('new_query')

    def test_keep_app_open(self, action):
        assert action.keep_app_open()

    def test_run(self, action, mocker, window):
        mocker.patch.object(action, 'set_position')
        action.run()
        window.input.set_text.assert_called_with('new_query')
        action.set_position.assert_called_with()
