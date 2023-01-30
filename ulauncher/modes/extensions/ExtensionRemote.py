import re
import logging
import os
from os.path import basename, exists
from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from shutil import move, rmtree
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ulauncher.config import API_VERSION, PATHS
from ulauncher.utils.version import satisfies
from ulauncher.utils.untar import untar
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionIncompatibleWarning

logger = logging.getLogger()


class ExtensionAlreadyInstalledWarning(Exception):
    pass


class ExtensionRemoteError(Exception):
    pass


class InvalidExtensionUrlWarning(Exception):
    pass


class ExtensionNetworkError(Exception):
    pass


class ExtensionRemote:
    url_match_pattern = r"^(?:git@|https?:\/\/)(?P<host>[^\/\:]+)[\/\:](?P<user>[^\/]+)\/(?P<repo>[^\/]+)"

    def __init__(self, url):
        match = re.match(self.url_match_pattern, url.lower(), re.I)
        if not match:
            raise InvalidExtensionUrlWarning(f"Invalid URL: {url}")

        self.host = match.group("host")
        self.user = match.group("user")
        self.repo = match.group("repo")
        if self.repo.endswith(".git"):
            self.repo = self.repo[:-4]
        self.url = f"https://{self.host}/{self.user}/{self.repo}"

        if "." not in self.host:
            self.extension_id = f"{self.host}.{self.user}.{self.repo}"
        else:
            domain, tld = self.host.rsplit(".", 1)
            self.extension_id = f"{tld}.{domain}.{self.user}.{self.repo}"

    def _get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            return f"{self.url}/-/archive/{commit}/{self.repo}-{commit}.tar.gz"
        return f"{self.url}/archive/{commit}.tar.gz"

    def _get_refs(self):
        refs = {}
        try:
            with urlopen(f"{self.url}/info/refs?service=git-upload-pack") as reader:
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
        output_dir_exists = exists(output_dir)

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
