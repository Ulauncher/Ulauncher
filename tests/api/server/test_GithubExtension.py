import io
from json import dumps

import pytest
from urllib.error import HTTPError

from ulauncher.utils.date import iso_to_datetime
from ulauncher.api.server.GithubExtension import GithubExtension, GithubExtensionError


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


class TestGithubExtension:

    @pytest.fixture
    def gh_ext(self) -> GithubExtension:
        return GithubExtension('https://github.com/Ulauncher/ulauncher-timer')

    def test_read_json(self, gh_ext: GithubExtension, mocker):
        urlopen = mocker.patch('ulauncher.api.server.GithubExtension.urlopen')
        urlopen.return_value.read.return_value = dumps(manifest_example).encode('utf-8')
        actual = gh_ext._read_json('master', 'manifest.json')
        assert actual == manifest_example

    def test_read_json__HTTPError__raises(self, gh_ext: GithubExtension, mocker):
        urlopen = mocker.patch('ulauncher.api.server.GithubExtension.urlopen')
        urlopen.side_effect = HTTPError('http://url', 404, 'urlopen error', {}, None)
        with pytest.raises(GithubExtensionError) as e:
            gh_ext._read_json('master', 'manifest.json')

        assert e.type == GithubExtensionError
        assert e.value.error_name == 'VersionsJsonNotFound'

    def test_read_versions(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, '_read_json')
        expected = [
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"},
            {"required_api_version": "^2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": "^2.3.1", "commit": "master"}
        ]
        gh_ext._read_json.return_value = expected
        actual = gh_ext.read_versions()
        assert actual == expected

    def test_read_versions__content_is_array__throws_error(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, '_read_json')
        gh_ext._read_json.return_value = ["^1.0.0", "^2.0.0"]
        with pytest.raises(GithubExtensionError):
            gh_ext.read_versions()

    def test_read_versions__value_is_number__throws_error(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, '_read_json')
        gh_ext._read_json.return_value = [
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"},
            {"required_api_version": "^2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": "^2.3.1", "commit": 1234}
        ]
        with pytest.raises(GithubExtensionError):
            gh_ext.read_versions()

    def test_read_versions__version_mismatch__raises(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, 'read_versions')
        gh_ext.read_versions.return_value = [
            {"required_api_version": "^1.0.0", "commit": "master"}
        ]
        expected_message = r'This extension is not compatible with current version Ulauncher extension API.*'
        with pytest.raises(GithubExtensionError, match=expected_message):
            gh_ext.find_compatible_version()

    def test_read_manifest(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, '_read_json')
        gh_ext._read_json.return_value = manifest_example
        manifest = gh_ext.read_manifest('abc123')
        assert manifest['required_api_version'] == '1'
        assert manifest['options']['query_debounce'] == 0.1
        assert manifest['preferences'][0]['type'] == 'keyword'

    def test_get_ext_id(self, gh_ext):
        assert gh_ext.get_ext_id() == 'com.github.ulauncher.ulauncher-timer'

    def test_validate_url(self, gh_ext):
        assert gh_ext.validate_url() is None

        with pytest.raises(GithubExtensionError):
            GithubExtension('http://github.com/Ulauncher/ulauncher-timer').validate_url()

        with pytest.raises(GithubExtensionError):
            GithubExtension('https://github.com/Ulauncher/ulauncher-timer/').validate_url()

    def test_get_download_url(self, gh_ext):
        assert gh_ext.get_download_url() == 'https://github.com/Ulauncher/ulauncher-timer/archive/master.zip'

    def test_get_commit(self, gh_ext, mocker):
        urlopen = mocker.patch('ulauncher.api.server.GithubExtension.urlopen')
        urlopen.return_value = io.BytesIO(dumps({
            'sha': '64e106c57ad90f9f02e9941dfa9780846b7457b9',
            'commit': {
                'committer': {
                    'date': '2017-05-01T07:30:39Z'
                }
            }
        }).encode('utf-8'))
        commit = gh_ext.get_commit('64e106c57')
        assert commit['sha'] == '64e106c57ad90f9f02e9941dfa9780846b7457b9'
        assert commit['time'] == iso_to_datetime('2017-05-01T07:30:39Z')

    def test_find_compatible_version(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, 'read_versions')
        mocker.patch.object(gh_ext, 'get_commit')
        gh_ext.read_versions.return_value = [
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"},
            {"required_api_version": "^2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": "^2.3.1", "commit": "master"}
        ]
        gh_ext.find_compatible_version()
        gh_ext.get_commit.assert_called_with("release-for-api-v2")

    def test_find_compatible_version__mult_compatible(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, 'read_versions')
        mocker.patch.object(gh_ext, 'get_commit')
        gh_ext.read_versions.return_value = [
            {"required_api_version": ">=2.0.0", "commit": "release-for-api-v2"},
            {"required_api_version": ">=1.3.1", "commit": "master"},
            {"required_api_version": "^1.0.0", "commit": "release-for-api-v1"}
        ]
        gh_ext.find_compatible_version()
        gh_ext.get_commit.assert_called_with("master")

    def test_find_compatible_version__invalid_range__raises(self, gh_ext, mocker):
        mocker.patch.object(gh_ext, 'read_versions')
        mocker.patch.object(gh_ext, 'get_commit')
        gh_ext.read_versions.return_value = [
            {"required_api_version": "-2.0.0", "commit": "master"}
        ]
        with pytest.raises(GithubExtensionError):
            gh_ext.find_compatible_version()
