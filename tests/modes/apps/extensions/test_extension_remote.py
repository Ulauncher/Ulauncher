from unittest.mock import MagicMock, patch

import pytest

from ulauncher.modes.extensions.extension_remote import (
    ExtensionRemote,
    InvalidExtensionRecoverableError,
    parse_extension_url,
)

# @todo: Add missing coverage for _get_refs, get_compatible_hash, download


class TestExtensionRemote:
    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote("https://github.com/Ulauncher/ulauncher-timer")

    def test_invalid_url(self) -> None:
        with pytest.raises(InvalidExtensionRecoverableError):
            ExtensionRemote("INVALID URL")


class TestParseExtensionUrl:
    def test_https_url(self) -> None:
        result = parse_extension_url("https://example.com/user/repo")
        assert result.remote_url == "https://example.com/user/repo"

    def test_http_url_converts_http_to_https(self) -> None:
        assert parse_extension_url("http://example.com/user/repo").remote_url.startswith("https://")

    def test_url_sanitization(self) -> None:
        assert parse_extension_url("  https://example.com/path  ").remote_url == "https://example.com/path"
        assert parse_extension_url("https://github.com/user/repo").remote_url == "https://github.com/user/repo.git"
        assert parse_extension_url("git@gitlab.com:user/repo.git").remote_url == "https://gitlab.com/user/repo.git"
        assert (
            parse_extension_url("https://github.com/user/repo/blob/master").remote_url
            == "https://github.com/user/repo.git"
        )
        assert parse_extension_url("https://gitlab.com/u/repo/issues").remote_url == "https://gitlab.com/u/repo.git"
        assert parse_extension_url("https://codeberg.org/u/repo/wiki").remote_url == "https://codeberg.org/u/repo.git"

    def test_browser_url(self) -> None:
        assert parse_extension_url("git@gitlab.com:user/repo.git").browser_url == "https://gitlab.com/user/repo"

    def test_ext_id(self) -> None:
        assert parse_extension_url("https://github.com/user/repo").ext_id == "com.github.user.repo"
        assert parse_extension_url("https://example.co.uk/user/repo").ext_id == "uk.co.example.user.repo"
        assert parse_extension_url("https://gitlab.com/user/repo/issues").ext_id == "com.gitlab.user.repo"
        assert parse_extension_url("https://local/path/to/extension").ext_id == "local.path.to.extension"
        assert parse_extension_url("https://localhost/extension").ext_id == "localhost.extension"

    def test_download_url_template(self) -> None:
        assert (
            parse_extension_url("https://github.com/user/repo").download_url_template
            == "https://github.com/user/repo/archive/[commit].tar.gz"
        )
        assert (
            parse_extension_url("https://codeberg.org/user/repo").download_url_template
            == "https://codeberg.org/user/repo/archive/[commit].tar.gz"
        )
        assert (
            parse_extension_url("https://gitlab.com/user/repo").download_url_template
            == "https://gitlab.com/user/repo/-/archive/[commit]/repo-[commit].tar.gz"
        )

    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_invalid_local_path_raises_assertion_error(self, mock_isdir: MagicMock) -> None:
        mock_isdir.return_value = False
        with pytest.raises(AssertionError):
            parse_extension_url("/nonexistent/path")

    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_local_file_path(self, mock_isdir: MagicMock) -> None:
        mock_isdir.return_value = True
        result = parse_extension_url("/local/path/to/extension")
        assert result == parse_extension_url("file:///local/path/to/extension")
        assert result.remote_url == "file:///local/path/to/extension"
        assert result.browser_url == "file:///local/path/to/extension"

    def test_empty_path_raises_assertion_error(self) -> None:
        with pytest.raises(AssertionError):
            parse_extension_url("https://example.com/")

    def test_no_host_no_file_protocol_raises_assertion_error(self) -> None:
        with pytest.raises(AssertionError):
            # This creates a URL with no host but protocol is https
            parse_extension_url("https:///user/repo")

    def test_valid_urls_ext_id(self) -> None:
        assert parse_extension_url("https://host.tld/user/repo").ext_id == "tld.host.user.repo"
        assert parse_extension_url("http://host/user/repo").ext_id == "host.user.repo"
        assert parse_extension_url("https://host.org/user/repo.git").ext_id == "org.host.user.repo.git"
        assert parse_extension_url("http://host/user/repo.git").ext_id == "host.user.repo.git"
        assert parse_extension_url("git@host.com:user/repo").ext_id == "com.host.user.repo"
        # verify sanitizing github/gitlab/codeberg urls, but leave all others
        assert parse_extension_url("https://github.com/user/repo/tree/HEAD").ext_id == "com.github.user.repo"
        assert parse_extension_url("https://gitlab.com/user/repo.git").ext_id == "com.gitlab.user.repo"
        assert parse_extension_url("https://other.host/a/b/c/d").ext_id == "host.other.a.b.c.d"
