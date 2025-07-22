from __future__ import annotations

import logging
import os
import subprocess
from os.path import basename, getmtime, isdir
from shutil import move, rmtree, which
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve

from ulauncher import api_version, paths
from ulauncher.modes.extensions.extension_manifest import ExtensionIncompatibleRecoverableError, ExtensionManifest
from ulauncher.utils.basedataclass import BaseDataClass
from ulauncher.utils.untar import untar
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class ExtensionRemoteError(Exception):
    pass


class InvalidExtensionRecoverableError(Exception):
    pass


class ExtensionNetworkError(Exception):
    pass


class UrlParseResult(BaseDataClass):
    ext_id: str
    remote_url: str
    browser_url: str | None = None
    download_url_template: str | None = None


class ExtensionRemote(UrlParseResult):
    url: str

    def __init__(self, url: str) -> None:
        try:
            self.url = url.strip()
            self.update(parse_extension_url(self.url))
        except Exception as e:
            logger.warning("Invalid URL: %s (%s: %s)", url, type(e).__name__, e)
            msg = f"Invalid URL: {url}"
            raise InvalidExtensionRecoverableError(msg) from e

        self._dir = f"{paths.USER_EXTENSIONS}/{self.ext_id}"
        self._git_dir = f"{paths.USER_EXTENSIONS}/.git/{self.ext_id}.git"

    def _get_refs(self) -> dict[str, str]:
        refs = {}
        ref = None
        try:
            if which("git"):
                if isdir(self._git_dir):
                    subprocess.run(
                        [
                            "git",
                            f"--git-dir={self._git_dir}",
                            "fetch",
                            "origin",
                            "+refs/heads/*:refs/heads/*",
                            "--prune",
                            "--prune-tags",
                        ],
                        check=True,
                    )
                else:
                    os.makedirs(self._git_dir)
                    subprocess.run(["git", "clone", "--bare", self.remote_url, self._git_dir], check=True)

                response = subprocess.check_output(["git", "ls-remote", self._git_dir]).decode().strip().split("\n")
            else:
                with urlopen(f"{self.remote_url}/info/refs?service=git-upload-pack") as reader:
                    response = reader.read().decode().strip().split("\n")
            if response:
                if response[-1] == "0000":
                    # Convert "smart" response, to more readable "dumb" response
                    # See https://www.git-scm.com/docs/http-protocol#_discovering_references
                    response = [r.split("\x00")[0][8:] if r.startswith("0000") else r[4:] for r in response[1:-1]]

                for row in response:
                    commit, ref = row.split()
                    refs[basename(ref)] = commit

        except Exception as e:
            if isinstance(e, (HTTPError, URLError)):
                msg = f'Could not access repository resource "{self.url}"'
                raise ExtensionNetworkError(msg) from e

            logger.warning("Unexpected error fetching extension versions '%s' (%s: %s)", self.url, type(e).__name__, e)
            msg = f'Could not fetch reference "{ref}" for {self.url}.'
            raise ExtensionRemoteError(msg) from e

        return refs

    def get_compatible_hash(self) -> str:
        """
        Returns the commit hash for the highest compatible version, matching using branch names
        and tags names starting with "apiv", ex "apiv3" and "apiv3.2"
        New method for v6. The new behavior is intentionally undocumented because we still
        want extension devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """
        remote_refs = self._get_refs()
        compatible = {
            ref: sha for ref, sha in remote_refs.items() if ref.startswith("apiv") and satisfies(api_version, ref[4:])
        }

        if compatible:
            return compatible[max(compatible)]

        # Try to get the commit ref for head, fallback on "HEAD" as a string as that can be used also
        return remote_refs.get("HEAD", "HEAD")

    def download(self, commit_hash: str | None = None, warn_if_overwrite: bool = False) -> tuple[str, float]:
        if not commit_hash:
            commit_hash = self.get_compatible_hash()
        output_dir_exists = isdir(self._dir)

        if output_dir_exists and warn_if_overwrite:
            logger.warning('Extension with URL "%s" is already installed. Overwriting', self.url)

        if self.download_url_template:
            with NamedTemporaryFile(suffix=".tar.gz", prefix="ulauncher_dl_") as tmp_file:
                download_url = self.download_url_template.replace("[commit]", commit_hash)
                urlretrieve(download_url, tmp_file.name)
                with TemporaryDirectory(prefix="ulauncher_ext_") as tmp_root_dir:
                    untar(tmp_file.name, tmp_root_dir)
                    subdirs = os.listdir(tmp_root_dir)
                    if len(subdirs) != 1:
                        msg = f"Invalid archive for {self.url}."
                        raise ExtensionRemoteError(msg)
                    tmp_dir = f"{tmp_root_dir}/{subdirs[0]}"
                    manifest = ExtensionManifest.load(f"{tmp_dir}/manifest.json")
                    if not satisfies(api_version, manifest.api_version):
                        if not satisfies("2.0", manifest.api_version):
                            msg = f"{manifest.name} does not support Ulauncher API v{api_version}."
                            raise ExtensionIncompatibleRecoverableError(msg)
                        logger.warning("Falling back on using API 2.0 version for %s.", self.url)

                    if output_dir_exists:
                        rmtree(self._dir)
                    move(tmp_dir, self._dir)
            commit_timestamp = getmtime(self._dir)
            return commit_hash, commit_timestamp

        if not which("git"):
            msg = "This extension URL can only be supported if you have git installed."
            raise ExtensionRemoteError(msg)

        os.makedirs(self._dir, exist_ok=True)
        subprocess.run(
            ["git", f"--git-dir={self._git_dir}", f"--work-tree={self._dir}", "checkout", commit_hash, "."],
            check=True,
        )
        commit_timestamp = float(
            subprocess.check_output(["git", f"--git-dir={self._git_dir}", "show", "-s", "--format=%ct", commit_hash])
            .decode()
            .strip()
        )
        return commit_hash, commit_timestamp


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

    assert path

    if url_parts.scheme in ("", "file"):
        assert isdir(url_parts.path)
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

    if not remote_url.startswith("file://"):
        assert host

    ext_id = ".".join(([*reversed(host.split("."))] if host else []) + path.split("/"))

    return UrlParseResult(
        ext_id=ext_id,
        remote_url=remote_url,
        browser_url=browser_url,
        download_url_template=download_url_template,
    )
