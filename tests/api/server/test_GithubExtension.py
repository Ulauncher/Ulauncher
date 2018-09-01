import io
import mock
import pytest

from json import dumps
from urllib.error import HTTPError

from ulauncher.api.server.GithubExtension import GithubExtension, InvalidGithubUrlError


class TestGithubExtension:

    @pytest.fixture
    def gh_ext(self):
        return GithubExtension('https://github.com/Ulauncher/ulauncher-timer')

    def test_get_ext_id(self, gh_ext):
        assert gh_ext.get_ext_id() == 'com.github.ulauncher.ulauncher-timer'

    def test_validate_url(self, gh_ext):
        assert gh_ext.validate_url() is None

        with pytest.raises(InvalidGithubUrlError):
            GithubExtension('http://github.com/Ulauncher/ulauncher-timer').validate_url()

        with pytest.raises(InvalidGithubUrlError):
            GithubExtension('https://github.com/Ulauncher/ulauncher-timer/').validate_url()

    def test_get_download_url(self, gh_ext):
        assert gh_ext.get_download_url() == 'https://github.com/Ulauncher/ulauncher-timer/archive/master.zip'

    def test_get_last_commit(self, gh_ext, mocker):
        urlopen = mocker.patch('ulauncher.api.server.GithubExtension.urlopen')
        urlopen.side_effect = [
            io.StringIO(dumps({'object': {'url': 'url123'}})),
            io.StringIO(dumps({'sha': '64e106c', 'committer': {'date': '2017-05-01T07:30:39Z'}}))
        ]
        info = gh_ext.get_last_commit()
        assert info['last_commit'] == '64e106c'
        assert info['last_commit_time'] == '2017-05-01T07:30:39Z'
