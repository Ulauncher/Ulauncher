import mock
import pytest

from ulauncher.api.server.ExtensionDb import ExtensionDb
from ulauncher.api.server.ExtensionRunner import ExtensionRunner
from ulauncher.api.server.ExtensionDownloader import ExtensionDownloader


class TestExtensionDownloader:

    @pytest.fixture
    def ext_db(self):
        return mock.create_autospec(ExtensionDb)

    @pytest.fixture
    def ext_runner(self):
        return mock.create_autospec(ExtensionRunner)

    @pytest.fixture
    def downloader(self, ext_db, ext_runner):
        return ExtensionDownloader(ext_db, ext_runner)

    @pytest.fixture(autouse=True)
    def gh_ext(self, mocker):
        gh_ext = mocker.patch('ulauncher.api.server.ExtensionDownloader.GithubExtension').return_value
        gh_ext.get_ext_id.return_value = 'com.github.ulauncher.ulauncher-timer'
        gh_ext.get_download_url.return_value = 'https://github.com/Ulauncher/ulauncher-timer/archive/master.zip'
        gh_ext.get_last_commit.return_value = {
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39Z'
        }

        return gh_ext

    @pytest.fixture(autouse=True)
    def download_zip(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.download_zip')

    @pytest.fixture(autouse=True)
    def unzip(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.unzip')

    @pytest.fixture(autouse=True)
    def datetime(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.datetime')
