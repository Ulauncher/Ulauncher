import pytest
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote, InvalidExtensionUrlWarning

# @todo: Add missing coverage for _get_refs, get_compatible_hash, download (with ExtensionAlreadyInstalledWarning)


class TestExtensionRemote:
    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote("https://github.com/Ulauncher/ulauncher-timer")

    def test_valid_urls_ext_id(self):
        assert ExtensionRemote("https://host.tld/user/repo").extension_id == "tld.host.user.repo"
        assert ExtensionRemote("http://host/user/repo").extension_id == "host.user.repo"
        assert ExtensionRemote("https://host.org/user/repo.git").extension_id == "org.host.user.repo.git"
        assert ExtensionRemote("http://host/user/repo.git").extension_id == "host.user.repo.git"
        assert ExtensionRemote("git@host.com:user/repo").extension_id == "com.host.user.repo"
        # verify sanitizing github/gitlab/codeberg urls, but leave all others
        assert ExtensionRemote("https://github.com/user/repo/tree/HEAD").extension_id == "com.github.user.repo"
        assert ExtensionRemote("https://gitlab.com/user/repo.git").extension_id == "com.gitlab.user.repo"
        assert ExtensionRemote("https://other.host/a/b/c/d").extension_id == "host.other.a.b.c.d"

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
