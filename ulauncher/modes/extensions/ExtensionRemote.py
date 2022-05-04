import codecs
import json
import re
import logging
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from typing import Optional, Tuple

from ulauncher.config import API_VERSION
from ulauncher.utils.date import iso_to_datetime
from ulauncher.utils.version import satisfies, valid_range
from ulauncher.api.shared.errors import ExtensionError, UlauncherAPIError

logger = logging.getLogger(__name__)

Commit = Tuple[str, datetime]


def json_fetch(url):
    try:
        return (json.loads(urlopen(url).read()), None)
    except Exception as e:
        return (None, e)


class ExtensionRemoteError(UlauncherAPIError):
    pass


class ExtensionRemote:
    url_match_pattern = r"^(?:git@|https:\/\/)(?P<host>[^\/]+)\/(?P<user>[^\/]+)\/(?P<repo>[^\/]+)"

    def __init__(self, url):
        self.url = url.lower()
        match = re.match(self.url_match_pattern, self.url, re.I)
        if not match:
            raise ExtensionRemoteError(f'Invalid URL: {url}', ExtensionError.InvalidUrl)

        self.user = match.group("user")
        self.repo = match.group("repo")
        self.host = match.group("host")

        if "." not in self.host:
            self.extension_id = f"{self.host}.{self.user}.{self.repo}"
        else:
            domain, tld = self.host.rsplit(".", 1)
            self.extension_id = f"{tld}.{domain}.{self.user}.{self.repo}"

        if self.host == "github.com":
            self.host_api = "https://api.github.com"
        elif self.host == "gitlab.com":
            host_api = "https://gitlab.com/api/v4"
            projects, err = json_fetch(f"{host_api}/users/{self.user}/projects?search={self.repo}")
            if err:
                raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from err
            project = next((p for p in projects if p["name"] == self.repo), None)

            self.host_api = f"{host_api}/projects/{project['id']}/repository"
        else:
            self.host_api = f"https://{self.host}/api/v1"

    def get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            return f'https://{self.host}/{self.user}/{self.repo}/-/archive/{commit}/{self.repo}-{commit}.tar.gz'
        return f'https://{self.host}/{self.user}/{self.repo}/archive/{commit}.tar.gz'

    def get_compatible_ref_from_tags(self) -> Optional[str]:
        tags = {}
        # pagination is only implemented for GitHub (default 30, max 100)
        tags_url = f"{self.host_api}/repos/{self.user}/{self.repo}/tags?per_page=100"
        if self.host == "gitlab.com":
            tags_url = f"{self.host_api}/tags?search=^apiv"
        tags_data, _ = json_fetch(tags_url)

        try:
            for tag in tags_data or []:
                if tag["name"].startswith("apiv") and satisfies(API_VERSION, tag["name"][4:]):
                    commit = tag["commit"]
                    verion = tag["name"][4:]
                    id = commit.get("sha", commit["id"])  # id fallback is needed for GitLab
                    tags[verion] = id
        except (KeyError, TypeError):
            pass

        return tags[max(tags)] if tags else None

    def get_compatible_ref_from_versions_json(self) -> Optional[str]:
        # This saves us a request compared to using the "raw" file API that needs to know the branch
        versions_url = f"{self.host_api}/repos/{self.user}/{self.repo}/contents/versions.json"
        if self.host == "gitlab.com":
            versions_url = f"{self.host_api}/files/versions.json?ref=HEAD"
        file_data, err = json_fetch(versions_url)
        versions = []

        if err:
            raise err

        if file_data:
            versions = json.loads(codecs.decode(file_data["content"].encode(), file_data["encoding"]))
            self.validate_versions(versions)

        versions_filter = (v['commit'] for v in versions if satisfies(API_VERSION, v['required_api_version']))
        return next(versions_filter, None)

    def get_commit(self, ref: str) -> Commit:
        # GitHub and GitLab supports accessing commits via other references like branch names
        # Gitea/Codeberg only supports commit hashes so we have to use the branches API
        api = "commits" if self.host == "github.com" else "branches"
        url = f"{self.host_api}/repos/{self.user}/{self.repo}/{api}/{ref}"
        if self.host == "gitlab.com":
            url = f"{self.host_api}/commits/{ref}"

        branch, err = json_fetch(url)

        if err:
            raise err

        try:
            if self.host == "github.com":
                id = branch["sha"]
                commit_time = iso_to_datetime(branch["commit"]["committer"]["date"])
            elif self.host == "gitlab.com":
                id = branch["id"]
                commit_time = datetime.strptime(branch["committed_date"][0:19], '%Y-%m-%dT%H:%M:%S')
            else:
                id = branch["commit"]["id"]
                commit_time = iso_to_datetime(branch["commit"]["timestamp"], False)
            return id, commit_time
        except (KeyError, TypeError):
            pass

        raise ExtensionRemoteError(
            f'Invalid metadata for commit url "{url}"',
            ExtensionError.InvalidVersionDeclaration
        )

    def get_latest_compatible_commit(self) -> Commit:
        """
        Finds first version that is compatible with users Ulauncher version.
        Returns a commit or branch/tag name and datetime.
        """

        ref = None

        try:
            ref = self.get_compatible_ref_from_tags() or self.get_compatible_ref_from_versions_json()

            if not ref:
                message = f"This extension is not compatible with your Ulauncher API version (v{API_VERSION})."
                raise ExtensionRemoteError(message, ExtensionError.Incompatible)

            return self.get_commit(ref)
        except URLError as e:
            if not ref:
                raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from e
            if getattr(e, "code") == 404:
                message = f'Invalid reference "{ref}" in version declaration.'
                raise ExtensionRemoteError(message, ExtensionError.InvalidVersionDeclaration) from e
            message = f'Could not fetch reference "{ref}".'
            raise ExtensionRemoteError(message, ExtensionError.Network) from e

    def validate_versions(self, versions) -> bool:
        missing = ExtensionError.MissingVersionDeclaration
        invalid = ExtensionError.InvalidVersionDeclaration

        if not versions:
            raise ExtensionRemoteError("Could not retrieve versions.json", missing)

        if not isinstance(versions, list):
            raise ExtensionRemoteError("versions.json should contain a list", invalid)
        for ver in versions:
            if not isinstance(ver, dict):
                raise ExtensionRemoteError("versions.json should contain a list of objects", invalid)
            if not isinstance(ver.get("commit"), str):
                raise ExtensionRemoteError("versions.json: commit should be a string", invalid)
            if not isinstance(ver.get("required_api_version"), str):
                raise ExtensionRemoteError("versions.json: required_api_version should be a string", invalid)
            if not valid_range(ver["required_api_version"]):
                raise ExtensionRemoteError(f'versions.json: Invalid range "{ver["required_api_version"]}"', invalid)

        return True
