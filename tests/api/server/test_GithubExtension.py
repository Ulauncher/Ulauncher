import io
import mock
import pytest

from json import dumps
from urllib2 import HTTPError

from ulauncher.api.server.GithubExtension import GithubExtension, GithubExtensionError


class TestGithubExtension:

    @pytest.fixture
    def gh_ext(self):
        return GithubExtension('https://github.com/Ulauncher/ulauncher-timer')

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
