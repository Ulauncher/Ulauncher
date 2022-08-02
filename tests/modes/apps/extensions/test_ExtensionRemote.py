import codecs
import pytest

from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote, InvalidExtensionUrlWarning

manifest_example = {'api_version': '1',
                    'authors': 'Aleksandr Gornostal',
                    'icon': 'images/timer.png',
                    'name': 'Timer',
                    'input_debounce': 0.1,
                    'preferences': [{'default_value': 'ti',
                                     'id': 'keyword',
                                     'name': 'My Timer',
                                     'type': 'keyword'}]}


def base64_file_attachment(data):
    content = codecs.encode(data.encode(), "base64").decode()
    return {"content": content, "encoding": "base64"}


class TestExtensionRemote:
    @pytest.fixture
    def json_fetch(self, mocker):
        return mocker.patch('ulauncher.modes.extensions.ExtensionRemote.json_fetch')

    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote('https://github.com/Ulauncher/ulauncher-timer')

    def test_ext_id(self, remote):
        assert remote.extension_id == 'com.github.ulauncher.ulauncher-timer'

    def test_invalid_urls(self):
        with pytest.raises(InvalidExtensionUrlWarning):
            ExtensionRemote('http://github.com/Ulauncher/ulauncher-timer')

        with pytest.raises(InvalidExtensionUrlWarning):
            ExtensionRemote('git@github.com/Ulauncher')

    def test_get_download_url(self, remote):
        assert remote.get_download_url('master') == 'https://github.com/ulauncher/ulauncher-timer/archive/master.tar.gz'

    def test_get_commit(self, remote, json_fetch):
        json_fetch.return_value = {
            'sha': '64e106c57ad90f9f02e9941dfa9780846b7457b9',
            'commit': {
                'committer': {
                    'date': '2017-05-01T07:30:39Z'
                }
            }
        }
        commit_sha, commit_time = remote.get_commit('64e106c57')
        assert commit_sha == '64e106c57ad90f9f02e9941dfa9780846b7457b9'
        assert commit_time == '2017-05-01T07:30:39'
