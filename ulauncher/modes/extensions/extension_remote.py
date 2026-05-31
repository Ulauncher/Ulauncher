from __future__ import annotations

import contextlib
import logging
import os
from os.path import basename, getmtime, isdir
from shutil import move, rmtree, which
from tarfile import TarError
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Callable
from urllib.parse import urlparse

from ulauncher import (
    api_version,
    paths,
)
from ulauncher.data import BaseDataClass
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
from ulauncher.utils.subprocess_utils import OnError, download_file, run_command
from ulauncher.utils.untar import untar
from ulauncher.utils.version import get_version, satisfies

logger = logging.getLogger(__name__)

RefsSuccess = Callable[["dict[str, str]"], None]
HashSuccess = Callable[[str], None]
DownloadSuccess = Callable[["tuple[str, float]"], None]


def _parse_refs_response(response_text: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    response = response_text.strip().split("\n")
    if response:
        if response[-1] == "0000":
            # Convert "smart" response, to more readable "dumb" response
            # See https://www.git-scm.com/docs/http-protocol#_discovering_references
            response = [r.split("\x00")[0][8:] if r.startswith("0000") else r[4:] for r in response[1:-1]]
        for row in response:
            if row:
                commit, ref = row.split()
                refs[basename(ref)] = commit
    return refs


class UrlParseResult(BaseDataClass):
    ext_id: str
    remote_url: str
    browser_url: str | None = None
    download_url_template: str | None = None


class ExtensionRemote(UrlParseResult):
    url: str
    target_dir: str

    def __init__(self, url: str) -> None:
        super().__init__()
        try:
            self.url = url.strip()
            self.update(parse_extension_url(self.url))
        except (ValueError, OSError) as e:
            logger.warning("Invalid URL: %s", url)
            msg = f"Invalid URL: {url}"
            raise ext_exceptions.UrlError(msg) from e

        self.target_dir = f"{paths.USER_EXTENSIONS}/{self.ext_id}"
        self._git_dir = f"{paths.USER_EXTENSIONS}/.git/{self.ext_id}.git"

    def _get_refs(self, on_success: RefsSuccess, on_error: OnError) -> None:
        network_error = ext_exceptions.NetworkError(f"Could not fetch remote {self.url}.")

        def on_ls_remote(stdout: str) -> None:
            try:
                refs = _parse_refs_response(stdout)
            except ValueError:
                on_error(network_error)
                return
            on_success(refs)

        def on_synced(_stdout: str) -> None:
            run_command(["git", "ls-remote", self._git_dir], on_ls_remote, lambda _error: on_error(network_error))

        def on_clone_failed(_error: Exception) -> None:
            # Otherwise the leftover empty dir sends future calls down the fetch path
            rmtree(self._git_dir, ignore_errors=True)
            on_error(network_error)

        if not which("git"):
            self._get_refs_http(on_success, on_error)
            return

        if isdir(self._git_dir):
            run_command(
                [
                    "git",
                    f"--git-dir={self._git_dir}",
                    "fetch",
                    "origin",
                    "+refs/heads/*:refs/heads/*",
                    "--prune",
                    "--prune-tags",
                ],
                on_synced,
                lambda _error: on_error(network_error),
            )
            return

        try:
            os.makedirs(self._git_dir)
        except OSError:
            on_error(network_error)
            return
        run_command(["git", "clone", "--bare", self.remote_url, self._git_dir], on_synced, on_clone_failed)

    def _get_refs_http(self, on_success: RefsSuccess, on_error: OnError) -> None:
        # git is not installed: fetch the dumb HTTP info/refs endpoint instead
        refs_url = f"{self.remote_url}/info/refs?service=git-upload-pack"
        with NamedTemporaryFile(suffix=".refs", prefix="ulauncher_refs_", delete=False) as tmp:
            refs_path = tmp.name

        def remove_tmp() -> None:
            with contextlib.suppress(OSError):
                os.remove(refs_path)

        def access_error() -> Exception:
            return ext_exceptions.NetworkError(f'Could not access repository resource "{self.url}"')

        def on_downloaded(_path: str) -> None:
            try:
                with open(refs_path) as reader:
                    refs = _parse_refs_response(reader.read())
            except (OSError, ValueError):
                on_error(access_error())
                return
            finally:
                remove_tmp()
            on_success(refs)

        def on_download_failed(_error: Exception) -> None:
            remove_tmp()
            on_error(access_error())

        download_file(refs_url, refs_path, on_downloaded, on_download_failed)

    def get_compatible_hash(self, on_success: HashSuccess, on_error: OnError) -> None:
        """
        Resolves the commit hash for the highest compatible version, matching using branch names
        and tags names starting with "apiv", ex "apiv3" and "apiv3.2"
        New method for v6. The new behavior is intentionally undocumented because we still
        want extension devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """

        def on_refs(remote_refs: dict[str, str]) -> None:
            # Strip the "apiv" prefix so keys are bare version strings ("3", "3.2") usable with get_version
            compatible = {
                ver: sha
                for ref, sha in remote_refs.items()
                if ref.startswith("apiv") and satisfies(api_version, (ver := ref[4:]))
            }
            if compatible:
                on_success(compatible[max(compatible, key=get_version)])
                return
            # Fall back on "HEAD" as a string as that can be used also
            on_success(remote_refs.get("HEAD", "HEAD"))

        self._get_refs(on_refs, on_error)

    def download(
        self,
        on_success: DownloadSuccess,
        on_error: OnError,
        commit_hash: str | None = None,
        warn_if_overwrite: bool = False,
    ) -> None:
        if commit_hash:
            self._download_with_hash(commit_hash, warn_if_overwrite, on_success, on_error)
            return

        def on_hash(resolved_hash: str) -> None:
            self._download_with_hash(resolved_hash, warn_if_overwrite, on_success, on_error)

        self.get_compatible_hash(on_hash, on_error)

    def _download_with_hash(
        self, commit_hash: str, warn_if_overwrite: bool, on_success: DownloadSuccess, on_error: OnError
    ) -> None:
        output_dir_exists = isdir(self.target_dir)
        if output_dir_exists and warn_if_overwrite:
            logger.info('Extension with URL "%s" is already installed. Updating', self.url)

        if self.download_url_template:
            download_url = self.download_url_template.replace("[commit]", commit_hash)
            with NamedTemporaryFile(suffix=".tar.gz", prefix="ulauncher_dl_", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            def remove_tmp() -> None:
                with contextlib.suppress(OSError):
                    os.remove(tmp_path)

            def on_downloaded(_path: str) -> None:
                try:
                    try:
                        result = self._extract_and_install(tmp_path, commit_hash, output_dir_exists)
                    except ext_exceptions.ExtensionError as install_error:
                        on_error(install_error)
                        return
                    on_success(result)
                finally:
                    remove_tmp()

            def on_download_failed(error: Exception) -> None:
                remove_tmp()
                on_error(ext_exceptions.RemoteError(f"Failed to download extension from {download_url}: {error}"))

            download_file(download_url, tmp_path, on_downloaded, on_download_failed)
            return

        if not which("git"):
            on_error(ext_exceptions.RemoteError("This extension URL can only be supported if you have git installed."))
            return

        try:
            os.makedirs(self.target_dir, exist_ok=True)
        except OSError as e:
            on_error(ext_exceptions.RemoteError(f"Failed to create extension directory {self.target_dir}: {e}"))
            return

        def on_timestamp(stdout: str) -> None:
            if not stdout:
                on_error(ext_exceptions.RemoteError(f"Failed to read commit {commit_hash}"))
                return
            try:
                commit_timestamp = float(stdout.strip())
            except ValueError:
                on_error(ext_exceptions.RemoteError(f"Failed to parse commit timestamp for {commit_hash}"))
                return
            on_success((commit_hash, commit_timestamp))

        def on_checkout(_stdout: str) -> None:
            run_command(
                ["git", f"--git-dir={self._git_dir}", "show", "-s", "--format=%ct", commit_hash],
                on_timestamp,
                lambda e: on_error(ext_exceptions.RemoteError(f"Failed to read commit {commit_hash}: {e}")),
            )

        def run_checkout() -> None:
            run_command(
                ["git", f"--git-dir={self._git_dir}", f"--work-tree={self.target_dir}", "checkout", commit_hash, "."],
                on_checkout,
                lambda e: on_error(ext_exceptions.RemoteError(f"Failed to checkout commit {commit_hash}: {e}")),
            )

        if not isdir(self._git_dir):
            # A pinned install passes commit_hash in and so skips get_compatible_hash(), which is
            # what clones the bare repo. Bootstrap it so the checkout below has a repo to read from.
            self._get_refs(lambda _refs: run_checkout(), on_error)
            return

        run_checkout()

    def _extract_and_install(self, tar_path: str, commit_hash: str, output_dir_exists: bool) -> tuple[str, float]:
        # All filesystem steps share the same failure semantics, so they live under one guard.
        # shutil.Error subclasses OSError, so move() failures are covered too. The intentional
        # RemoteError/CompatibilityError raises are ExtensionError (not OSError) and propagate as-is.
        # This must not let a raw OSError escape: it runs inside a Gio callback, where an uncaught
        # exception would be swallowed and hang _run_gio_blocking instead of reaching the caller.
        try:
            with TemporaryDirectory(prefix="ulauncher_ext_") as tmp_root_dir:
                untar(tar_path, tmp_root_dir)
                subdirs = os.listdir(tmp_root_dir)
                if len(subdirs) != 1:
                    msg = f"Invalid archive for {self.url}."
                    raise ext_exceptions.RemoteError(msg)
                tmp_dir = f"{tmp_root_dir}/{subdirs[0]}"
                manifest = ExtensionManifest.load(f"{tmp_dir}/manifest.json")
                if not satisfies(api_version, manifest.api_version):
                    if not satisfies("2.0", manifest.api_version):
                        msg = f"{manifest.name} does not support Ulauncher API v{api_version}."
                        raise ext_exceptions.CompatibilityError(msg)
                    logger.warning("Falling back on using API 2.0 version for %s.", self.url)
                if output_dir_exists:
                    rmtree(self.target_dir)
                move(tmp_dir, self.target_dir)
            return commit_hash, getmtime(self.target_dir)
        except (TarError, OSError) as e:
            msg = f"Failed to install extension from {tar_path}: {e}"
            raise ext_exceptions.RemoteError(msg) from e


def parse_extension_url(input_url: str) -> UrlParseResult:
    """
    Parses the extension URL and returns a dictionary.
    Raises AssertionError if the URL is invalid.
    """
    browser_url: str | None = None
    download_url_template: str | None = None
    input_url_is_ssl = False
    input_url = input_url.strip()
    remote_url = input_url.lower()
    # Convert SSH endpoint to URL
    # This might not be a real supported URL for the remote host, but we still need this step to proceed
    if remote_url.startswith("git@"):
        input_url_is_ssl = True
        remote_url = "https://" + remote_url[4:].replace(":", "/")

    url_parts = urlparse(remote_url)
    path = url_parts.path[1:]
    host = url_parts.netloc
    remote_url = f"https://{host}/{path}"

    if not path:
        msg = f"Invalid URL: {input_url}"
        raise ValueError(msg)

    if url_parts.scheme in ("", "file"):
        if not isdir(url_parts.path):
            msg = f"Invalid path: {input_url}"
            raise ValueError(msg)
        browser_url = remote_url = f"file:///{path}"

    elif host in ("github.com", "gitlab.com", "codeberg.org"):
        # Sanitize URLs with known hosts and invalid trailing paths like /blob/master or /issues, /wiki etc
        user, repo, *_ = path.split("/", 2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        path = f"{user}/{repo}"
        browser_url = base_url = f"https://{host}/{path}"
        remote_url = f"{base_url}.git"
        download_url_template = (
            f"{base_url}/-/archive/[commit]/{repo}-[commit].tar.gz"
            if host == "gitlab.com"
            else f"{base_url}/archive/[commit].tar.gz"
        )

    elif input_url_is_ssl:
        logger.warning("Can not safely derive HTTPS URL from SSL URL input '%s', Assuming: '%s'", input_url, remote_url)

    if not remote_url.startswith("file://") and not host:
        msg = f"Invalid URL: {input_url}"
        raise ValueError(msg)

    ext_id = ".".join(([*reversed(host.split("."))] if host else []) + path.split("/"))

    return UrlParseResult(
        ext_id=ext_id,
        remote_url=remote_url,
        browser_url=browser_url,
        download_url_template=download_url_template,
    )
