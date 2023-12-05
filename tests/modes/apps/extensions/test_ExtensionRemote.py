import pytest

from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote, InvalidExtensionUrlWarning

# @todo: Add missing coverage for _get_refs, get_compatible_hash, download


class TestExtensionRemote:
    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote("https://github.com/Ulauncher/ulauncher-timer")

    def test_valid_urls_ext_id(self):
        assert ExtensionRemote("https://host.tld/user/repo").ext_id == "tld.host.user.repo"
        assert ExtensionRemote("http://host/user/repo").ext_id == "host.user.repo"
        assert ExtensionRemote("https://host.org/user/repo.git").ext_id == "org.host.user.repo.git"
        assert ExtensionRemote("http://host/user/repo.git").ext_id == "host.user.repo.git"
        assert ExtensionRemote("git@host.com:user/repo").ext_id == "com.host.user.repo"
        # verify sanitizing github/gitlab/codeberg urls, but leave all others
        assert ExtensionRemote("https://github.com/user/repo/tree/HEAD").ext_id == "com.github.user.repo"
        assert ExtensionRemote("https://gitlab.com/user/repo.git").ext_id == "com.gitlab.user.repo"
        assert ExtensionRemote("https://other.host/a/b/c/d").ext_id == "host.other.a.b.c.d"

    def test_invalid_url(self):
        with pytest.raises(InvalidExtensionUrlWarning):
            ExtensionRemote("INVALID URL")

    def test_get_download_url(self):
        assert (
            ExtensionRemote("https://github.com/user/repo")._get_download_url("master")
            == "https://github.com/user/repo/archive/master.tar.gz"
        )
        assert (
            ExtensionRemote("https://gitlab.com/user/repo")._get_download_url("master")
            == "https://gitlab.com/user/repo/-/archive/master/repo-master.tar.gz"
        )
