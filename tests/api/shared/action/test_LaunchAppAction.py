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
