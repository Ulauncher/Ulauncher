import logging
import os
from os.path import basename, getmtime, isdir
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from shutil import move, rmtree
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ulauncher.config import API_VERSION, PATHS
from ulauncher.utils.version import satisfies
from ulauncher.utils.untar import untar
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionIncompatibleWarning

logger = logging.getLogger()
db = ExtensionDb.load()


class ExtensionAlreadyInstalledWarning(Exception):
    pass


class ExtensionRemoteError(Exception):
    pass


class InvalidExtensionUrlWarning(Exception):
    pass


class ExtensionNetworkError(Exception):
    pass


class ExtensionRemote:
    def __init__(self, url: str):
        try:
            self.url = url.strip().lower()
            # Reformat to URL format if it's SSH
            if self.url.startswith("git@"):
                self.url = "git://" + self.url[4:].replace(":", "/")

            url_parts = urlparse(self.url)
            assert url_parts.scheme and url_parts.netloc and url_parts.path

            self.host = url_parts.netloc
            self.path = url_parts.path[1:]

            if self.host in ("github.com", "gitlab.com", "codeberg.org"):
                # Sanitize URLs with known hosts and invalid trailing paths like /blob/master or /issues, /wiki etc
                user, repo, *_ = self.path.split("/", 2)
                if repo.endswith(".git"):
                    repo = repo[:-4]
                self.path = f"{user}/{repo}"
            elif url_parts.scheme != "https":
                logger.warning('Unsupported URL protocol: "%s". Will attempt to use HTTPS', url_parts.scheme)
            self.url = f"https://{self.host}/{self.path}"

        except Exception as e:
            raise InvalidExtensionUrlWarning(f"Invalid URL: {url}") from e

        self.extension_id = ".".join(
            [
                *reversed(self.host.split(".")),
                *self.path.split("/"),
            ]
        )

    def _get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            repo = self.path.split("/")[1]
            return f"{self.url}/-/archive/{commit}/{repo}-{commit}.tar.gz"
        return f"{self.url}/archive/{commit}.tar.gz"

    def _get_refs(self):
        refs = {}
        url = f"{self.url}.git" if self.host in ("github.com", "gitlab.com", "codeberg.org") else self.url
        try:
            with urlopen(f"{url}/info/refs?service=git-upload-pack") as reader:
                response = reader.read().decode().split("\n")
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
                raise ExtensionNetworkError(f'Could not access repository resource "{self.url}"') from e

            logger.warning("Unexpected error fetching extension versions '%s' (%s: %s)", self.url, type(e).__name__, e)
            raise ExtensionRemoteError(f'Could not fetch reference "{ref}" for {self.url}.') from e

        return refs

    def get_compatible_hash(self) -> str:
        """
        Returns the commit hash for the highest compatible version, matching using branch names
        and tags names starting with "apiv", ex "apiv3" and "apiv3.2"
        New method for v6. The new behavior is intentionally undocumented because we still
        want extension devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """
        remote_refs = self._get_refs()
        compatible = {ref: sha for ref, sha in remote_refs.items() if satisfies(API_VERSION, ref[4:])}

        if compatible:
            return compatible[max(compatible)]

        # Try to get the commit ref for head, fallback on "HEAD" as a string as that can be used also
        return remote_refs.get("HEAD", "HEAD")

    def download(self, commit_hash=None, overwrite=False):
        if not commit_hash:
            commit_hash = self.get_compatible_hash()
        url = self._get_download_url(commit_hash)
        output_dir = f"{PATHS.EXTENSIONS}/{self.extension_id}"
        output_dir_exists = isdir(output_dir)

        if output_dir_exists and not overwrite:
            raise ExtensionAlreadyInstalledWarning(f'Extension with URL "{url}" is already installed.')

        with NamedTemporaryFile(suffix=".tar.gz", prefix="ulauncher_dl_") as tmp_file:
            urlretrieve(url, tmp_file.name)
            with TemporaryDirectory(prefix="ulauncher_ext_") as tmp_dir:
                untar(tmp_file.name, tmp_dir)
                subdirs = os.listdir(tmp_dir)
                if len(subdirs) != 1:
                    raise ExtensionRemoteError(f"Invalid archive for {self.url}.")
                tmp_dir = f"{tmp_dir}/{subdirs[0]}"
                manifest = ExtensionManifest.new_from_file(f"{tmp_dir}/manifest.json")
                if not satisfies(API_VERSION, manifest.api_version):
                    if not satisfies("2.0", manifest.api_version):
                        raise ExtensionIncompatibleWarning(
                            f"{manifest.name} does not support Ulauncher API v{API_VERSION}."
                        )
                    logger.warning("Falling back on using API 2.0 version for %s.", self.url)

                if output_dir_exists:
                    rmtree(output_dir)
                move(tmp_dir, output_dir)

        ext_mtime = getmtime(output_dir)
        ext_record = ExtensionRecord(
            id=self.extension_id,
            last_commit=commit_hash,
            last_commit_time=datetime.fromtimestamp(ext_mtime).isoformat(),
            updated_at=datetime.now().isoformat(),
            url=self.url,
        )
        db.save({self.extension_id: ext_record})
