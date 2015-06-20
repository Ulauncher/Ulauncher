import mock
import pytest
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction


class TestSetUserQueryAction:

    @pytest.fixture
    def action(self):
        return SetUserQueryAction('new_query')

    def test_keep_app_open(self, action):
        assert action.keep_app_open()

    def test_run(self, action, mocker):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        action.run()
        UlauncherWindow.get_instance.return_value.input.set_text.assert_called_with('new_query')
        UlauncherWindow.get_instance.return_value.input.set_position.assert_called_with(len('new_query'))
