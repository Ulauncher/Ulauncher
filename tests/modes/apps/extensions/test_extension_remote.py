import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from ulauncher.modes.extensions.extension_remote import (
    ExtensionRemote,
    InvalidExtensionRecoverableError,
    UrlParseResult,
    generate_extension_id,
    git_remote_url,
    parse_extension_url,
)

# @todo: Add missing coverage for _get_refs, get_compatible_hash, download


class TestExtensionRemote:
    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote("https://github.com/Ulauncher/ulauncher-timer")

    def test_valid_urls_ext_id(self) -> None:
        assert ExtensionRemote("https://host.tld/user/repo").ext_id == "tld.host.user.repo"
        assert ExtensionRemote("http://host/user/repo").ext_id == "host.user.repo"
        assert ExtensionRemote("https://host.org/user/repo.git").ext_id == "org.host.user.repo.git"
        assert ExtensionRemote("http://host/user/repo.git").ext_id == "host.user.repo.git"
        assert ExtensionRemote("git@host.com:user/repo").ext_id == "com.host.user.repo"
        # verify sanitizing github/gitlab/codeberg urls, but leave all others
        assert ExtensionRemote("https://github.com/user/repo/tree/HEAD").ext_id == "com.github.user.repo"
        assert ExtensionRemote("https://gitlab.com/user/repo.git").ext_id == "com.gitlab.user.repo"
        assert ExtensionRemote("https://other.host/a/b/c/d").ext_id == "host.other.a.b.c.d"

    def test_invalid_url(self) -> None:
        with pytest.raises(InvalidExtensionRecoverableError):
            ExtensionRemote("INVALID URL")

    def test_get_download_url(self) -> None:
        assert (
            ExtensionRemote("https://github.com/user/repo")._get_download_url("master")
            == "https://github.com/user/repo/archive/master.tar.gz"
        )
        assert (
            ExtensionRemote("https://gitlab.com/user/repo")._get_download_url("master")
            == "https://gitlab.com/user/repo/-/archive/master/repo-master.tar.gz"
        )


class TestParseExtensionUrl:
    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_https_url(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("https://example.com/user/repo")

        assert result == UrlParseResult(
            use_git=True, url="https://example.com/user/repo", path="user/repo", protocol="https", host="example.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_http_url_converts_to_https(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("http://example.com/user/repo")

        assert result == UrlParseResult(
            use_git=True, url="https://example.com/user/repo", path="user/repo", protocol="https", host="example.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_ssh_url_reformatting(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("git@github.com:user/repo")

        assert result == UrlParseResult(
            use_git=False,  # don't use git for github, gitlab, codeberg URLs
            url="https://github.com/user/repo",
            path="user/repo",
            protocol="https",
            host="github.com",
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_local_file_path(self, mock_isdir: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_isdir.return_value = True
        result = parse_extension_url("/local/path/to/extension")

        assert result == UrlParseResult(
            use_git=True,
            url="file:///local/path/to/extension",
            path="local/path/to/extension",
            protocol="file",
            host="",
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_github_url_sanitization(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("https://github.com/user/repo/blob/master")

        assert result == UrlParseResult(
            use_git=False, url="https://github.com/user/repo", path="user/repo", protocol="https", host="github.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_gitlab_url_sanitization(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("https://gitlab.com/user/repo/issues")

        assert result == UrlParseResult(
            use_git=False, url="https://gitlab.com/user/repo", path="user/repo", protocol="https", host="gitlab.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_codeberg_url_sanitization(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("https://codeberg.org/user/repo/wiki")

        assert result == UrlParseResult(
            use_git=False,
            url="https://codeberg.org/user/repo",
            path="user/repo",
            protocol="https",
            host="codeberg.org",
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_git_extension_removal(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("https://github.com/user/repo.git")

        assert result == UrlParseResult(
            use_git=False, url="https://github.com/user/repo", path="user/repo", protocol="https", host="github.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_no_git_available(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        result = parse_extension_url("https://example.com/user/repo")

        assert result == UrlParseResult(
            use_git=False, url="https://example.com/user/repo", path="user/repo", protocol="https", host="example.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_url_with_whitespace(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        result = parse_extension_url("  https://example.com/user/repo  ")

        assert result == UrlParseResult(
            use_git=True, url="https://example.com/user/repo", path="user/repo", protocol="https", host="example.com"
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_file_protocol_url(self, mock_isdir: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_isdir.return_value = True
        result = parse_extension_url("file:///local/path/to/extension")

        assert result == UrlParseResult(
            use_git=True,
            url="file:///local/path/to/extension",
            path="local/path/to/extension",
            protocol="file",
            host="",
        )

    @patch("ulauncher.modes.extensions.extension_remote.which")
    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_invalid_local_path_raises_assertion_error(self, mock_isdir: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_isdir.return_value = False

        with pytest.raises(AssertionError):
            parse_extension_url("/nonexistent/path")

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_empty_path_raises_assertion_error(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"

        with pytest.raises(AssertionError):
            parse_extension_url("https://example.com/")

    @patch("ulauncher.modes.extensions.extension_remote.which")
    def test_no_host_no_file_protocol_raises_assertion_error(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"

        with pytest.raises(AssertionError):
            # This creates a URL with no host but protocol is https
            parse_extension_url("https:///user/repo")


class TestGenerateExtensionId:
    def test_with_host_and_path(self) -> None:
        assert generate_extension_id("github.com", "user/repo") == "com.github.user.repo"
        assert generate_extension_id("example.co.uk", "user/repo") == "uk.co.example.user.repo"
        assert generate_extension_id("gitlab.com", "group/subgroup/repo") == "com.gitlab.group.subgroup.repo"

    def test_with_empty_host(self) -> None:
        assert generate_extension_id("", "local/path/to/extension") == "local.path.to.extension"

    def test_with_single_component_host_and_path(self) -> None:
        assert generate_extension_id("localhost", "extension") == "localhost.extension"


class TestGitRemoteUrl:
    def test_git_remote_url_with_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(["git", "init"], cwd=temp_dir, check=True)

            test_url = "https://github.com/user/repo.git"
            subprocess.run(["git", "remote", "add", "origin", test_url], cwd=temp_dir, check=True)

            result = git_remote_url(temp_dir)
            assert result == test_url

    def test_git_remote_url_without_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(["git", "init"], cwd=temp_dir, check=True)

            result = git_remote_url(temp_dir)
            assert result is None

    def test_git_remote_url_not_a_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = git_remote_url(temp_dir)
            assert result is None
