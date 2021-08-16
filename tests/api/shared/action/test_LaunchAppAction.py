import mock
import pytest

from ulauncher.api.shared.action.LaunchAppAction import LaunchAppAction


class TestLaunchAppAction:

    @pytest.fixture
    def filename(self):
        return mock.Mock()

    @pytest.fixture
    def action(self, filename):
        return LaunchAppAction(filename)

    def test_keep_app_open(self, action):
        assert not action.keep_app_open()

#   def test_run(self, action, mocker, filename):
#       read_desktop_file = mocker.patch('ulauncher.api.shared.action.LaunchAppAction.read_desktop_file')
#       action.run()
#       read_desktop_file.assert_called_with(filename)
#       read_desktop_file.return_value.launch.assert_called_with()
