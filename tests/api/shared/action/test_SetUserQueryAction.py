import pytest

from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction


class TestSetUserQueryAction:

    @pytest.fixture(autouse=True)
    def window(self, mocker):
        UlauncherWindow = mocker.patch('ulauncher.ui.windows.UlauncherWindow.UlauncherWindow')
        return UlauncherWindow.get_instance.return_value

    @pytest.fixture
    def action(self):
        return SetUserQueryAction('new query')

    def test_keep_app_open(self, action):
        assert action.keep_app_open

    def test_update_query(self, action, window):
        action._update_query()
        window.input.set_text.assert_called_with('new query')
