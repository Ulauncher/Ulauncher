import mock
import pytest

from ulauncher.util.Settings import Settings
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.api.server.ExtensionAutoupdater import ExtensionAutoupdater
from ulauncher.api.server.ExtensionDownloader import (ExtensionDownloader, ExtensionIsUpToDateError)


class TestExtensionAutoupdater:

    @pytest.fixture
    def ext_downloader(self):
        return mock.create_autospec(ExtensionDownloader)

    @pytest.fixture
    def ul_window(self):
        return mock.create_autospec(UlauncherWindow)

    @pytest.fixture
    def settings(self):
        return mock.create_autospec(Settings)

    @pytest.fixture
    def autoupdater(self, ext_downloader, ul_window, settings):
        return ExtensionAutoupdater(ext_downloader, ul_window, settings)

    def test_update_success(self, autoupdater, ext_downloader, mocker):
        find_extensions = mocker.patch('ulauncher.api.server.ExtensionAutoupdater.find_extensions')
        find_extensions.return_value = [('my-ext-id', '/ext/path')]
        autoupdater._update()

        ext_downloader.update.assert_called_with('my-ext-id')
