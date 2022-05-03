import codecs
import json
import pytest

from ulauncher.utils.date import iso_to_datetime
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote, ExtensionRemoteError

manifest_example = {'required_api_version': '1',
                    'description': 'Countdown timer with notifications',
                    'developer_name': 'Aleksandr Gornostal',
                    'icon': 'images/timer.png',
                    'name': 'Timer',
                    'options': {'query_debounce': 0.1},
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

    def test_validate_versions(self, remote):
        with pytest.raises(ExtensionRemoteError, match="Could not retrieve versions.json"):
            assert remote.validate_versions(None)
            assert remote.validate_versions([])
        with pytest.raises(ExtensionRemoteError, match="should contain a list"):
            assert remote.validate_versions(True)
            assert remote.validate_versions(1)
        with pytest.raises(ExtensionRemoteError, match="should contain a list of objects"):
            assert remote.validate_versions(["^1.0.0", "^2.0.0"])
        with pytest.raises(ExtensionRemoteError, match="commit should be a string"):
            assert remote.validate_versions([{}, {}])
            assert remote.validate_versions([{"required_api_version": "3"}])
            assert remote.validate_versions([{"commit": 1234}])
        with pytest.raises(ExtensionRemoteError, match="required_api_version should be a string"):
            assert remote.validate_versions([{"commit": "asdf", "required_api_version": 1}])
            assert remote.validate_versions([{"commit": "asdf", "required_api_version": 3.1}])
        with pytest.raises(ExtensionRemoteError, match="Invalid range"):
            assert remote.validate_versions([{"commit": "asdf", "required_api_version": "4-1"}])
            assert remote.validate_versions([{"commit": "asdf", "required_api_version": "2 to 3"}])
            assert remote.validate_versions([{"commit": "asdf", "required_api_version": "four"}])

        assert remote.validate_versions([{"required_api_version": "2 - 3", "commit": "main"}])

    def test_get_compatible_ref_from_versions_json_mismatch__raises(self, remote, mocker):
        mocker.patch.object(remote, 'get_compatible_ref_from_versions_json')
        remote.get_compatible_ref_from_versions_json.return_value = None
        with pytest.raises(ExtensionRemoteError, match="not compatible with your Ulauncher API version"):
            remote.get_latest_compatible_commit()

    def test_ext_id(self, remote):
        assert remote.extension_id == 'com.github.ulauncher.ulauncher-timer'

    def test_invalid_urls(self):
        with pytest.raises(ExtensionRemoteError):
            ExtensionRemote('http://github.com/Ulauncher/ulauncher-timer')

        with pytest.raises(ExtensionRemoteError):
            ExtensionRemote('git@github.com/Ulauncher')

    def test_get_download_url(self, remote):
        assert remote.get_download_url('master') == 'https://github.com/ulauncher/ulauncher-timer/archive/master.tar.gz'

    def test_get_commit(self, remote, json_fetch):
        json_fetch.return_value = ({
            'sha': '64e106c57ad90f9f02e9941dfa9780846b7457b9',
            'commit': {
                'committer': {
                    'date': '2017-05-01T07:30:39Z'
                }
            }
        }, None)
        commit_sha, commit_time = remote.get_commit('64e106c57')
        assert commit_sha == '64e106c57ad90f9f02e9941dfa9780846b7457b9'
        assert commit_time == iso_to_datetime('2017-05-01T07:30:39Z')

    def test_get_compatible_ref_from_versions_json(self, remote, json_fetch):
        json_fetch.return_value = (base64_file_attachment(json.dumps([
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"},
            {"required_api_version": "^2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": "^2.3.1", "commit": "master"}
        ])), None)
        assert remote.get_compatible_ref_from_versions_json() == "release-for-api-v2"

    def test_get_compatible_ref_from_versions_json__mult_compatible(self, remote, json_fetch):
        json_fetch.return_value = (base64_file_attachment(json.dumps([
            {"required_api_version": "2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": "~1.3.1", "commit": "master"},
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"}
        ])), None)
        assert remote.get_compatible_ref_from_versions_json() == "release-for-api-v2"
