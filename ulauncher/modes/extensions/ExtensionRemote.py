import re
import logging
from os.path import basename
from urllib.request import urlopen

from ulauncher.config import API_VERSION
from ulauncher.utils.version import satisfies

logger = logging.getLogger()


class InvalidExtensionUrlWarning(Exception):
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

    def get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            return f"{self.url}/-/archive/{commit}/{self.repo}-{commit}.tar.gz"
        return f"{self.url}/archive/{commit}.tar.gz"

    def get_refs(self):
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
            logger.warning("Unexpected error fetching extension versions '%s' (%s: %s)", self.url, type(e).__name__, e)

        return refs

    def get_compatible_hash(self) -> str:
        """
        Returns the commit hash for the highest compatible version, matching using branch names
        and tags names starting with "apiv", ex "apiv3" and "apiv3.2"
        New method for v6. The new behavior is intentionally undocumented because we still
        want extension devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """
        remote_refs = self.get_refs()
        compatible = {ref: sha for ref, sha in remote_refs.items() if satisfies(API_VERSION, ref[4:])}

        if compatible:
            return compatible[max(compatible)]

        # Try to get the commit ref for head, fallback on "HEAD" as a string as that can be used also
        return remote_refs.get("HEAD", "HEAD")
