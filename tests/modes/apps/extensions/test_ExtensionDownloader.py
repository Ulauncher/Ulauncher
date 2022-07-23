from unittest import mock
import pytest

from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionDownloader import (
    ExtensionDownloader, ExtensionAlreadyInstalledWarning)


class TestExtensionDownloader:

    @pytest.fixture
    def ext_db(self):
        return mock.create_autospec(ExtensionDb)

    @pytest.fixture
    def downloader(self, ext_db):
        return ExtensionDownloader(ext_db)

    @pytest.fixture(autouse=True)
    def gh_ext(self, mocker):
        gh_ext = mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.ExtensionRemote').return_value
        gh_ext.extension_id = 'com.github.ulauncher.ulauncher-timer'
        gh_ext.get_download_url.return_value = 'https://github.com/Ulauncher/ulauncher-timer/archive/master.tar.gz'
        gh_ext.get_latest_compatible_commit.return_value = ('64e106c', '2017-05-01T07:30:39')
        return gh_ext

    @pytest.fixture(autouse=True)
    def download_tarball(self, mocker):
        return mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.download_tarball')

    @pytest.fixture(autouse=True)
    def ExtensionRemote(self, mocker):
        return mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.ExtensionRemote')

    @pytest.fixture(autouse=True)
    def untar(self, mocker):
        return mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.untar')

    @pytest.fixture(autouse=True)
    def datetime(self, mocker):
        return mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.datetime')

    # pylint: disable=unused-argument,too-many-arguments
    def test_download(self, downloader, mocker, untar, ext_db, download_tarball, datetime):
        os = mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.os')
        os.path.exists.return_value = False
        assert downloader.download('https://github.com/Ulauncher/ulauncher-timer') == \
            'com.github.ulauncher.ulauncher-timer'

        untar.assert_called_with(download_tarball.return_value, mock.ANY)
        ext_db.save.assert_called_with({'com.github.ulauncher.ulauncher-timer': {
            'id': 'com.github.ulauncher.ulauncher-timer',
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39'
        }})

    # pylint: disable=unused-argument
    def test_download_raises_AlreadyDownloadedError(self, downloader, ext_db, mocker):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.get.return_value = {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': '2017-01-01',
            'last_commit': 'aDbc',
            'last_commit_time': '2017-01-01'
        }
        os = mocker.patch('ulauncher.modes.extensions.ExtensionDownloader.os')
        os.path.exists.return_value = True

        with pytest.raises(ExtensionAlreadyInstalledWarning):
            downloader.download('https://github.com/Ulauncher/ulauncher-timer')

    def test_update(self, downloader, ext_db, gh_ext, download_tarball, untar, datetime):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.get.return_value = ExtensionRecord(
            id=ext_id,
            url='https://github.com/Ulauncher/ulauncher-timer',
            updated_at='2017-01-01',
            last_commit='aDbc',
            last_commit_time='2017-01-01'
        )

        assert downloader.update(ext_id)

        download_tarball.assert_called_with(gh_ext.get_download_url.return_value)
        untar.assert_called_with(download_tarball.return_value, mock.ANY)
        ext_db.save.assert_called_with({ext_id: {
            'id': ext_id,
            'url': 'https://github.com/Ulauncher/ulauncher-timer',
            'updated_at': datetime.now.return_value.isoformat.return_value,
            'last_commit': '64e106c',
            'last_commit_time': '2017-05-01T07:30:39'
        }})

    def test_check_update__returns_new_version(self, downloader, ext_db, gh_ext):
        ext_id = 'com.github.ulauncher.ulauncher-timer'
        ext_db.get.return_value = ExtensionRecord(
            id=ext_id,
            url='https://github.com/Ulauncher/ulauncher-timer',
            updated_at='2017-01-01',
            last_commit='a8827b723',
            last_commit_time='2017-01-01'
        )

        assert downloader.check_update(ext_id) == (True, '64e106c', '2017-05-01T07:30:39')
