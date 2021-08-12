import mock
import pytest

from ulauncher.utils.date import iso_to_datetime
from ulauncher.api.server.ExtensionDb import ExtensionDb
from ulauncher.api.server.ExtensionRunner import ExtensionRunner
from ulauncher.api.server.ExtensionDownloader import (
    ExtensionDownloader, ExtensionDownloaderError, ExtensionIsUpToDateError)


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
        gh_ext.get_download_url.return_value = 'https://github.com/Ulauncher/ulauncher-timer/tarball/master'
        gh_ext.get_last_commit.return_value = {
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39'
        }
        gh_ext.find_compatible_version.return_value = {
            'sha': '64e106c',
            'time': iso_to_datetime('2017-05-01T07:30:39Z')
        }

        return gh_ext

    @pytest.fixture(autouse=True)
    def download_tarball(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.download_tarball')

    @pytest.fixture(autouse=True)
    def GithubExtension(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.GithubExtension')

    @pytest.fixture(autouse=True)
    def untar(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.untar')

    @pytest.fixture(autouse=True)
    def datetime(self, mocker):
        return mocker.patch('ulauncher.api.server.ExtensionDownloader.datetime')

    # pylint: disable=unused-argument,too-many-arguments
    def test_download(self, downloader, mocker, untar, ext_db, download_tarball, datetime):
        os = mocker.patch('ulauncher.api.server.ExtensionDownloader.os')
        os.path.exists.return_value = False
        assert downloader.download('https://github.com/Ulauncher/ulauncher-timer') == \
            'com.github.ulauncher.ulauncher-timer'

        untar.assert_called_with(download_tarball.return_value, mock.ANY)
        ext_db.put.assert_called_with('com.github.ulauncher.ulauncher-timer', {
            'id': 'com.github.ulauncher.ulauncher-timer',
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39'
        })

    # pylint: disable=unused-argument
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

        with pytest.raises(ExtensionDownloaderError):
            assert downloader.download('https://github.com/Ulauncher/ulauncher-timer')

    def test_update(self, downloader, ext_db, ext_runner, gh_ext, download_tarball, untar, datetime):
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

        download_tarball.assert_called_with(gh_ext.get_download_url.return_value)
        untar.assert_called_with(download_tarball.return_value, mock.ANY)
        ext_runner.stop.assert_called_with(ext_id)
        ext_runner.run.assert_called_with(ext_id)
        ext_db.put.assert_called_with(ext_id, {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39'
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

    def test_get_new_version__returns_new_version(self, downloader, ext_db, ext_runner, gh_ext):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': 'a8827b723',
            'last_commit_time': '2017-01-01'
        }

        assert downloader.get_new_version(ext_id) == gh_ext.get_last_commit.return_value
