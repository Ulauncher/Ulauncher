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
        assert ExtensionRemote("https://host.org/user/repo.git").extension_id == "org.host.user.repo"
        assert ExtensionRemote("http://host/user/repo.git").extension_id == "host.user.repo"
        assert ExtensionRemote("git@host.com:user/repo.git").extension_id == "com.host.user.repo"
        assert ExtensionRemote("https://host/user/repo/tree/master").extension_id == "host.user.repo"

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
