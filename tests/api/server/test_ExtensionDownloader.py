import io
import mock
import pytest

from json import dumps
from urllib.error import HTTPError

from ulauncher.api.server.ExtensionDb import ExtensionDb
from ulauncher.api.server.ExtensionRunner import ExtensionRunner
from ulauncher.api.server.ExtensionDownloader import (ExtensionDownloader, ExtensionIsUpToDateError,
                                                      AlreadyDownloadedError)


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

    def test_download(self, downloader, ext_db, ext_runner, unzip, download_zip, datetime):
        ext_db.find.return_value = None

        assert downloader.download('https://github.com/Ulauncher/ulauncher-timer') == \
            'com.github.ulauncher.ulauncher-timer'

        unzip.assert_called_with(download_zip.return_value, mock.ANY)
        ext_db.put.assert_called_with('com.github.ulauncher.ulauncher-timer', {
            'id': 'com.github.ulauncher.ulauncher-timer',
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39Z'
        })

    def test_download_raises_AlreadyDownloadedError(self, downloader, ext_db, ext_runner, mocker):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': 'aDbc',
            'last_commit_time': '2017-01-01'
        }
        os = mocker.patch('ulauncher.api.server.ExtensionDownloader.os')
        os.path.exists.return_value = True

        with pytest.raises(AlreadyDownloadedError):
            assert downloader.download('https://github.com/Ulauncher/ulauncher-timer')

    def test_update(self, downloader, ext_db, ext_runner, gh_ext, download_zip, unzip, datetime):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': 'aDbc',
            'last_commit_time': '2017-01-01'
        }
        ext_runner.is_running.return_value = True

        assert downloader.update(ext_id)

        download_zip.assert_called_with(gh_ext.get_download_url.return_value)
        unzip.assert_called_with(download_zip.return_value, mock.ANY)
        ext_runner.stop.assert_called_with(ext_id)
        ext_runner.run.assert_called_with(ext_id)
        ext_db.put.assert_called_with(ext_id, {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39Z'
        })

    def test_get_new_version_raises_ExtensionIsUpToDateError(self, downloader, ext_db):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39Z'
        }

        with pytest.raises(ExtensionIsUpToDateError):
            downloader.get_new_version(ext_id)

    def test_get_new_version_returns_new_version(self, downloader, ext_db, ext_runner, gh_ext):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': 'a8827b723',
            'last_commit_time': '2017-01-01'
        }

        assert downloader.get_new_version(ext_id) == gh_ext.get_last_commit.return_value
