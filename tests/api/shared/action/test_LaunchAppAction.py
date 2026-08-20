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

    @pytest.fixture
    def read_desktop_file(self, mocker):
        return mocker.patch('ulauncher.api.shared.action.LaunchAppAction.read_desktop_file')

    @pytest.fixture
    def spawn_async(self, mocker):
        return mocker.patch('ulauncher.api.shared.action.LaunchAppAction.GLib.spawn_async')

    def test_keep_app_open(self, action):
        assert not action.keep_app_open()

    def test_run__unreadable_desktop_file__spawns_nothing(self, read_desktop_file, spawn_async):
        read_desktop_file.return_value = None
        LaunchAppAction('/usr/share/applications/gone.desktop').run()
        assert not spawn_async.called

    def test_run__desktop_file_without_exec__spawns_nothing(self, read_desktop_file, spawn_async):
        app = read_desktop_file.return_value
        app.get_id.return_value = 'no-exec.desktop'
        app.get_string.return_value = None
        app.get_boolean.return_value = False
        LaunchAppAction('/usr/share/applications/no-exec.desktop').run()
        assert not spawn_async.called

#   def test_run(self, action, mocker, filename):
#       read_desktop_file = mocker.patch('ulauncher.api.shared.action.LaunchAppAction.read_desktop_file')
#       action.run()
#       read_desktop_file.assert_called_with(filename)
#       read_desktop_file.return_value.launch.assert_called_with()
