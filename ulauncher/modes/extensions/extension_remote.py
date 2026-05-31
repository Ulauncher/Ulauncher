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
from ulauncher.utils.subprocess_utils import download_file, run_command
from ulauncher.utils.untar import untar
from ulauncher.utils.version import get_version, satisfies

logger = logging.getLogger(__name__)

RefsCallback = Callable[["dict[str, str] | None", "Exception | None"], None]
HashCallback = Callable[["str | None", "Exception | None"], None]
DownloadCallback = Callable[["tuple[str, float] | None", "Exception | None"], None]


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

    def _get_refs(self, callback: RefsCallback) -> None:
        def parse_response(response_text: str) -> dict[str, str]:
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

        def on_ls_remote(stdout: str | None, error: Exception | None) -> None:
            if error:
                callback(None, ext_exceptions.NetworkError(f"Could not fetch remote {self.url}."))
                return
            try:
                refs = parse_response(stdout or "")
            except ValueError:
                callback(None, ext_exceptions.NetworkError(f"Could not fetch remote {self.url}."))
                return
            callback(refs, None)

        def after_sync(_stdout: str | None, error: Exception | None) -> None:
            if error:
                callback(None, ext_exceptions.NetworkError(f"Could not fetch remote {self.url}."))
                return
            run_command(["git", "ls-remote", self._git_dir], on_ls_remote)

        if which("git"):
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
                    after_sync,
                )
            else:
                try:
                    os.makedirs(self._git_dir)
                except OSError:
                    callback(None, ext_exceptions.NetworkError(f"Could not fetch remote {self.url}."))
                    return
                run_command(["git", "clone", "--bare", self.remote_url, self._git_dir], after_sync)
            return

        # git is not installed: fetch the dumb HTTP info/refs endpoint instead
        refs_url = f"{self.remote_url}/info/refs?service=git-upload-pack"
        with NamedTemporaryFile(suffix=".refs", prefix="ulauncher_refs_", delete=False) as tmp:
            refs_path = tmp.name

        def on_refs_downloaded(_path: str | None, error: Exception | None) -> None:
            try:
                if error:
                    callback(None, ext_exceptions.NetworkError(f'Could not access repository resource "{self.url}"'))
                    return
                with open(refs_path) as reader:
                    refs = parse_response(reader.read())
            except (OSError, ValueError):
                callback(None, ext_exceptions.NetworkError(f'Could not access repository resource "{self.url}"'))
                return
            finally:
                with contextlib.suppress(OSError):
                    os.remove(refs_path)
            callback(refs, None)

        download_file(refs_url, refs_path, on_refs_downloaded)

    def get_compatible_hash(self, callback: HashCallback) -> None:
        """
        Resolves the commit hash for the highest compatible version, matching using branch names
        and tags names starting with "apiv", ex "apiv3" and "apiv3.2"
        New method for v6. The new behavior is intentionally undocumented because we still
        want extension devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """

        def on_refs(remote_refs: dict[str, str] | None, error: Exception | None) -> None:
            if error or remote_refs is None:
                callback(None, error)
                return
            # Strip the "apiv" prefix so keys are bare version strings ("3", "3.2") usable with get_version
            compatible = {
                ver: sha
                for ref, sha in remote_refs.items()
                if ref.startswith("apiv") and satisfies(api_version, (ver := ref[4:]))
            }
            if compatible:
                callback(compatible[max(compatible, key=get_version)], None)
                return
            # Fall back on "HEAD" as a string as that can be used also
            callback(remote_refs.get("HEAD", "HEAD"), None)

        self._get_refs(on_refs)

    def download(
        self,
        callback: DownloadCallback,
        commit_hash: str | None = None,
        warn_if_overwrite: bool = False,
    ) -> None:
        if commit_hash:
            self._download_with_hash(commit_hash, warn_if_overwrite, callback)
            return

        def on_hash(resolved_hash: str | None, error: Exception | None) -> None:
            if error or resolved_hash is None:
                callback(None, error)
                return
            self._download_with_hash(resolved_hash, warn_if_overwrite, callback)

        self.get_compatible_hash(on_hash)

    def _download_with_hash(self, commit_hash: str, warn_if_overwrite: bool, callback: DownloadCallback) -> None:
        output_dir_exists = isdir(self.target_dir)
        if output_dir_exists and warn_if_overwrite:
            logger.info('Extension with URL "%s" is already installed. Updating', self.url)

        if self.download_url_template:
            download_url = self.download_url_template.replace("[commit]", commit_hash)
            with NamedTemporaryFile(suffix=".tar.gz", prefix="ulauncher_dl_", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            def on_downloaded(_path: str | None, error: Exception | None) -> None:
                try:
                    if error:
                        callback(
                            None,
                            ext_exceptions.RemoteError(f"Failed to download extension from {download_url}: {error}"),
                        )
                        return
                    try:
                        result = self._extract_and_install(tmp_path, commit_hash, output_dir_exists)
                    except ext_exceptions.ExtensionError as install_error:
                        callback(None, install_error)
                        return
                    callback(result, None)
                finally:
                    with contextlib.suppress(OSError):
                        os.remove(tmp_path)

            download_file(download_url, tmp_path, on_downloaded)
            return

        if not which("git"):
            callback(
                None, ext_exceptions.RemoteError("This extension URL can only be supported if you have git installed.")
            )
            return

        os.makedirs(self.target_dir, exist_ok=True)

        def after_checkout(_stdout: str | None, error: Exception | None) -> None:
            if error:
                callback(None, ext_exceptions.RemoteError(f"Failed to checkout commit {commit_hash}: {error}"))
                return

            def after_show(stdout: str | None, show_error: Exception | None) -> None:
                if show_error or stdout is None:
                    callback(None, ext_exceptions.RemoteError(f"Failed to checkout commit {commit_hash}: {show_error}"))
                    return
                try:
                    commit_timestamp = float(stdout.strip())
                except ValueError:
                    callback(None, ext_exceptions.RemoteError(f"Failed to parse commit timestamp for {commit_hash}"))
                    return
                callback((commit_hash, commit_timestamp), None)

            run_command(
                ["git", f"--git-dir={self._git_dir}", "show", "-s", "--format=%ct", commit_hash],
                after_show,
            )

        run_command(
            ["git", f"--git-dir={self._git_dir}", f"--work-tree={self.target_dir}", "checkout", commit_hash, "."],
            after_checkout,
        )

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
