import os
import pytest
import mock
from ulauncher.utils.Settings import Settings


class TestSettings:

    @pytest.fixture
    def filename(self, tmpdir):
        return os.path.join(str(tmpdir), 'ulauncher.json')

    @pytest.fixture
    def settings(self):
        return Settings()

    def test_load_from_file(self, settings, filename):
        settings.load_from_file(filename)
        settings.set_property('hotkey-show-app', 'xyz')
        assert settings.get_property('hotkey-show-app') == 'xyz'

    def test_save_to_file(self, settings, filename):
        settings.load_from_file(filename)
        settings.set_property('hotkey-show-app', 'xyz')
        settings.save_to_file()
        with open(filename, 'r') as f:
            assert '"hotkey-show-app": "xyz"' in f.read()

    def test_without_file(self, settings):
        assert settings.get_property('show-indicator-icon')
        settings.set_property('show-indicator-icon', False)
        assert not settings.get_property('show-indicator-icon')

    def test_subscribe_to_property_change_signal(self, settings):
        on_notify = mock.Mock()
        settings.connect("notify::hotkey-show-app", on_notify)

        settings.set_property("hotkey-show-app", "foo")
        on_notify.assert_called_with(settings, mock.ANY)

    def test_get_property_default(self, settings, filename):
        with open(filename, 'w') as f:
            f.write("{}")
        settings.load_from_file(filename)
        assert settings.get_property('theme-name') == 'light'
