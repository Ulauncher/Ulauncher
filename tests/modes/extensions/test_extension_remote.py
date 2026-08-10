from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest

from ulauncher import api_version
from ulauncher.data import Err, Ok
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_remote import (
    ExtensionRemote,
    UrlParseResult,
    parse_extension_url,
)


def parse_ok(url: str) -> UrlParseResult:
    result = parse_extension_url(url)
    assert isinstance(result, Ok)
    return result.value


# @todo: remaining uncovered paths: the no-git HTTP info/refs fallback, the fetch/clone
# failure before ls-remote, and download() resolving the hash itself (no commit_hash given).


class TestExtensionRemote:
    @pytest.fixture
    def remote(self) -> ExtensionRemote:
        return ExtensionRemote("https://github.com/Ulauncher/ulauncher-timer")

    def test_invalid_url(self) -> None:
        with pytest.raises(ext_exceptions.UrlError):
            ExtensionRemote("INVALID URL")


class TestParseExtensionUrl:
    def test_https_url(self) -> None:
        result = parse_ok("https://example.com/user/repo")
        assert result.remote_url == "https://example.com/user/repo"

    def test_http_url_converts_http_to_https(self) -> None:
        assert parse_ok("http://example.com/user/repo").remote_url.startswith("https://")

    def test_url_sanitization(self) -> None:
        assert parse_ok("  https://example.com/path  ").remote_url == "https://example.com/path"
        assert parse_ok("https://github.com/user/repo").remote_url == "https://github.com/user/repo.git"
        assert parse_ok("git@gitlab.com:user/repo.git").remote_url == "https://gitlab.com/user/repo.git"
        assert parse_ok("https://github.com/user/repo/blob/master").remote_url == "https://github.com/user/repo.git"
        assert parse_ok("https://gitlab.com/u/repo/issues").remote_url == "https://gitlab.com/u/repo.git"
        assert parse_ok("https://codeberg.org/u/repo/wiki").remote_url == "https://codeberg.org/u/repo.git"

    def test_browser_url(self) -> None:
        assert parse_ok("git@gitlab.com:user/repo.git").browser_url == "https://gitlab.com/user/repo"

    def test_ext_id(self) -> None:
        assert parse_ok("https://github.com/user/repo").ext_id == "com.github.user.repo"
        assert parse_ok("https://example.co.uk/user/repo").ext_id == "uk.co.example.user.repo"
        assert parse_ok("https://gitlab.com/user/repo/issues").ext_id == "com.gitlab.user.repo"
        assert parse_ok("https://local/path/to/extension").ext_id == "local.path.to.extension"
        assert parse_ok("https://localhost/extension").ext_id == "localhost.extension"

    def test_download_url_template(self) -> None:
        assert (
            parse_ok("https://github.com/user/repo").download_url_template
            == "https://github.com/user/repo/archive/[commit].tar.gz"
        )
        assert (
            parse_ok("https://codeberg.org/user/repo").download_url_template
            == "https://codeberg.org/user/repo/archive/[commit].tar.gz"
        )
        assert (
            parse_ok("https://gitlab.com/user/repo").download_url_template
            == "https://gitlab.com/user/repo/-/archive/[commit]/repo-[commit].tar.gz"
        )

    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_invalid_local_path_returns_error(self, mock_isdir: MagicMock) -> None:
        mock_isdir.return_value = False
        result = parse_extension_url("/nonexistent/path")
        assert isinstance(result, Err)
        assert "Invalid path" in result.error

    @patch("ulauncher.modes.extensions.extension_remote.isdir")
    def test_local_file_path(self, mock_isdir: MagicMock) -> None:
        mock_isdir.return_value = True
        result = parse_ok("/local/path/to/extension")
        assert result == parse_ok("file:///local/path/to/extension")
        assert result.remote_url == "file:///local/path/to/extension"
        assert result.browser_url == "file:///local/path/to/extension"

    def test_empty_path_returns_error(self) -> None:
        result = parse_extension_url("https://example.com/")
        assert isinstance(result, Err)
        assert "Invalid URL" in result.error

    def test_known_host_without_repo_returns_error(self) -> None:
        for url in ("https://github.com/owner", "https://gitlab.com/owner/", "git@codeberg.org:owner"):
            result = parse_extension_url(url)
            assert isinstance(result, Err)
            assert "Invalid URL" in result.error

    def test_no_host_no_file_protocol_returns_error(self) -> None:
        # This creates a URL with no host but protocol is https
        result = parse_extension_url("https:///user/repo")
        assert isinstance(result, Err)
        assert "Invalid URL" in result.error

    def test_valid_urls_ext_id(self) -> None:
        assert parse_ok("https://host.tld/user/repo").ext_id == "tld.host.user.repo"
        assert parse_ok("http://host/user/repo").ext_id == "host.user.repo"
        assert parse_ok("https://host.org/user/repo.git").ext_id == "org.host.user.repo.git"
        assert parse_ok("http://host/user/repo.git").ext_id == "host.user.repo.git"
        assert parse_ok("git@host.com:user/repo").ext_id == "com.host.user.repo"
        # verify sanitizing github/gitlab/codeberg urls, but leave all others
        assert parse_ok("https://github.com/user/repo/tree/HEAD").ext_id == "com.github.user.repo"
        assert parse_ok("https://gitlab.com/user/repo.git").ext_id == "com.gitlab.user.repo"
        assert parse_ok("https://other.host/a/b/c/d").ext_id == "host.other.a.b.c.d"


def _call(
    start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None],
) -> tuple[Any, Exception | None]:
    """Invoke a callback-based method whose mocked dependencies fire synchronously."""
    box: dict[str, Any] = {}
    start(
        lambda result: box.update(result=result, error=None),
        lambda error: box.update(result=None, error=error),
    )
    return box.get("result"), box.get("error")


class TestGetCompatibleHash:
    @patch("ulauncher.modes.extensions.extension_remote.which", return_value="/usr/bin/git")
    @patch("ulauncher.modes.extensions.extension_remote.isdir", return_value=True)
    @patch("ulauncher.modes.extensions.extension_remote.run_command")
    def test_returns_compatible_apiv_ref(self, mock_run: MagicMock, *_: Any) -> None:
        ls_remote_output = f"def456\trefs/heads/apiv{api_version}\nabc123\tHEAD\n"

        def side_effect(cmd: list[str], on_success: Callable[[Any], None], _on_error: Any, **_kw: Any) -> None:
            on_success(ls_remote_output if "ls-remote" in cmd else "")

        mock_run.side_effect = side_effect
        remote = ExtensionRemote("https://github.com/user/repo")
        result, error = _call(remote.get_compatible_hash)
        assert error is None
        assert result == "def456"

    @patch("ulauncher.modes.extensions.extension_remote.which", return_value="/usr/bin/git")
    @patch("ulauncher.modes.extensions.extension_remote.isdir", return_value=True)
    @patch("ulauncher.modes.extensions.extension_remote.run_command")
    def test_maps_command_failure_to_network_error(self, mock_run: MagicMock, *_: Any) -> None:
        def side_effect(
            cmd: list[str], on_success: Callable[[Any], None], on_error: Callable[[Any], None], **_kw: Any
        ) -> None:
            if "ls-remote" in cmd:
                on_error(subprocess.CalledProcessError(128, cmd))
            else:
                on_success("")

        mock_run.side_effect = side_effect
        remote = ExtensionRemote("https://github.com/user/repo")
        result, error = _call(remote.get_compatible_hash)
        assert result is None
        assert isinstance(error, ext_exceptions.NetworkError)


def _download(remote: ExtensionRemote, target_dir: str) -> tuple[Any, Exception | None]:
    return _call(lambda on_success, on_error: remote.download(target_dir, on_success, on_error, commit_hash="abc123"))


class TestDownload:
    target_dir: str

    @pytest.fixture(autouse=True)
    def _staging_dir(self, tmp_path: Path) -> None:
        # download() replaces the target wholesale, so it must never be pointed at a real install
        self.target_dir = str(tmp_path / "staging")

    @patch("ulauncher.modes.extensions.extension_remote.which", return_value="/usr/bin/git")
    @patch("ulauncher.modes.extensions.extension_remote.run_command")
    def test_git_checkout_path_returns_hash_and_timestamp(self, mock_run: MagicMock, *_: Any) -> None:
        def side_effect(cmd: list[str], on_success: Callable[[Any], None], _on_error: Any, **_kw: Any) -> None:
            on_success("1700000000\n" if "show" in cmd else "")

        mock_run.side_effect = side_effect
        # example.com has no download_url_template, so download() takes the git checkout path
        remote = ExtensionRemote("https://example.com/user/repo")
        result, error = _download(remote, self.target_dir)
        assert error is None
        assert result == ("abc123", 1700000000.0)

    @patch("ulauncher.modes.extensions.extension_remote.download_file")
    def test_download_failure_maps_to_remote_error(self, mock_download: MagicMock) -> None:
        def side_effect(_url: str, _dest: str, _on_success: Any, on_error: Callable[[Any], None]) -> None:
            on_error(OSError("boom"))

        mock_download.side_effect = side_effect
        remote = ExtensionRemote("https://github.com/user/repo")
        result, error = _download(remote, self.target_dir)
        assert result is None
        assert isinstance(error, ext_exceptions.RemoteError)

    @patch("ulauncher.modes.extensions.extension_remote.which", return_value="/usr/bin/git")
    @patch("ulauncher.modes.extensions.extension_remote.run_command")
    def test_unparsable_commit_timestamp_maps_to_remote_error(self, mock_run: MagicMock, *_: Any) -> None:
        # A raw ValueError from float() would otherwise escape the Gio callback and hang the bridge.
        def side_effect(cmd: list[str], on_success: Callable[[Any], None], _on_error: Any, **_kw: Any) -> None:
            on_success("not-a-timestamp" if "show" in cmd else "")

        mock_run.side_effect = side_effect
        remote = ExtensionRemote("https://example.com/user/repo")
        result, error = _download(remote, self.target_dir)
        assert result is None
        assert isinstance(error, ext_exceptions.RemoteError)

    @patch("ulauncher.modes.extensions.extension_remote.which", return_value="/usr/bin/git")
    @patch("ulauncher.modes.extensions.extension_remote.run_command")
    def test_out_of_range_commit_timestamp_maps_to_remote_error(self, mock_run: MagicMock, *_: Any) -> None:
        # The repo picks this number. No date can hold it, so save_installed_state would raise
        # after the new files were already swapped in.
        def side_effect(cmd: list[str], on_success: Callable[[Any], None], _on_error: Any, **_kw: Any) -> None:
            on_success("99999999999999" if "show" in cmd else "")

        mock_run.side_effect = side_effect
        remote = ExtensionRemote("https://example.com/user/repo")
        result, error = _download(remote, self.target_dir)
        assert result is None
        assert isinstance(error, ext_exceptions.RemoteError)

    @patch("ulauncher.modes.extensions.extension_remote.untar", side_effect=OSError("disk full"))
    @patch("ulauncher.modes.extensions.extension_remote.download_file")
    def test_install_oserror_maps_to_remote_error(self, mock_download: MagicMock, *_: Any) -> None:
        # A raw OSError from the filesystem install steps must be mapped, not escape the callback.
        def side_effect(_url: str, dest: str, on_success: Callable[[Any], None], _on_error: Any) -> None:
            on_success(dest)

        mock_download.side_effect = side_effect
        remote = ExtensionRemote("https://github.com/user/repo")
        result, error = _download(remote, self.target_dir)
        assert result is None
        assert isinstance(error, ext_exceptions.RemoteError)
