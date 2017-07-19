import io
import mock
import pytest

from json import dumps
from urllib2 import HTTPError

from ulauncher.api.server.ExtensionDb import ExtensionDb
from ulauncher.api.server.ExtensionRunner import ExtensionRunner
from ulauncher.api.server.ExtensionDownloader import ExtensionDownloader, get_ext_meta, get_zip_url


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

    def test_download(self, downloader, ext_db, ext_runner, mocker):
        ext_db.find.return_value = None
        get_ext_meta = mocker.patch('ulauncher.api.server.ExtensionDownloader.get_ext_meta')
        get_ext_meta.return_value = {'last_commit': 'abc', 'last_commit_time_iso': '2017-01-01'}
        download_zip = mocker.patch('ulauncher.api.server.ExtensionDownloader.download_zip')
        unzip = mocker.patch('ulauncher.api.server.ExtensionDownloader.unzip')
        time = mocker.patch('ulauncher.api.server.ExtensionDownloader.time')

        assert downloader.download('https://github.com/name/project') == 'com.github.name.project'

        unzip.assert_called_with(download_zip.return_value, mock.ANY)
        ext_db.put.assert_called_with('com.github.name.project', {
            'id': 'com.github.name.project',
            'url': 'https://github.com/name/project',
            'updated_at': time.return_value,
            'last_commit': 'abc',
            'last_commit_time_iso': '2017-01-01'
        })

    def test_update(self, downloader, ext_db, ext_runner, mocker):
        ext_id = 'com.github.name.project'
        ext_db.find.return_value = {
            'id': ext_id,
            'url': 'https://github.com/name/project',
            'updated_at': 11111111111,
            'last_commit': 'abc',
            'last_commit_time_iso': '2017-01-01'
        }
        get_ext_meta = mocker.patch('ulauncher.api.server.ExtensionDownloader.get_ext_meta')
        get_ext_meta.return_value = {'last_commit': 'abd', 'last_commit_time_iso': '2017-01-02'}
        ext_runner.is_running.return_value = True
        download_zip = mocker.patch('ulauncher.api.server.ExtensionDownloader.download_zip')
        unzip = mocker.patch('ulauncher.api.server.ExtensionDownloader.unzip')
        time = mocker.patch('ulauncher.api.server.ExtensionDownloader.time')

        assert downloader.update(ext_id)

        download_zip.assert_called_with('https://github.com/name/project')
        unzip.assert_called_with(download_zip.return_value, mock.ANY)
        ext_runner.stop.assert_called_with(ext_id)
        ext_runner.run.assert_called_with(ext_id)
        ext_db.put.assert_called_with(ext_id, {
            'id': ext_id,
            'url': 'https://github.com/name/project',
            'updated_at': time.return_value,
            'last_commit': 'abd',
            'last_commit_time_iso': '2017-01-02'
        })


def test_get_ext_meta__returns_last_commit_info(mocker):
    urlopen = mocker.patch('ulauncher.api.server.ExtensionDownloader.urlopen')
    urlopen.side_effect = [
        io.StringIO(dumps({'object': {'url': 'url123'}}).decode('utf-8')),
        io.StringIO(dumps({'sha': '64e106c', 'committer': {'date': '2017-05-01T07:30:39Z'}}).decode('utf-8'))
    ]
    meta = get_ext_meta('https://github.com/Ulauncher/Ulauncher-timer')
    assert meta['last_commit'] == '64e106c'
    assert meta['last_commit_time_iso'] == '2017-05-01T07:30:39Z'


def test_get_ext_meta__raises(mocker):
    urlopen = mocker.patch('ulauncher.api.server.ExtensionDownloader.urlopen')
    urlopen.side_effect = Exception()
    with pytest.raises(Exception):
        get_ext_meta('https://github.com/doesnt/exist')


def test_get_zip_url():
    assert get_zip_url('https://github.com/a/b') == 'https://github.com/a/b/archive/master.zip'
