import codecs
import json
import re
import logging
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from typing import List, Tuple

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
            self.host_api = "https://gitlab.com/api/v4"
            projects, err = json_fetch(f"{self.host_api}/users/{self.user}/projects?search={self.repo}")
            if err:
                raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from err
            project = next((p for p in projects if p["name"] == self.repo), None)
            self.gitlab_default_branch = project["default_branch"]
            self.gitlab_project_id = project["id"]
        else:
            self.host_api = f"https://{self.host}/api/v1"

    def get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            return f'https://{self.host}/{self.user}/{self.repo}/-/archive/{commit}/{self.repo}-{commit}.tar.gz'
        return f'https://{self.host}/{self.user}/{self.repo}/archive/{commit}.tar.gz'

    def get_versions(self) -> List:
        # This saves us a request compared to using the "raw" file API that needs to know the branch
        versions_url = f"{self.host_api}/repos/{self.user}/{self.repo}/contents/versions.json"
        if self.host == "gitlab.com":
            versions_url = (
                f"{self.host_api}/projects/{self.gitlab_project_id}"
                f"/repository/files/versions.json?ref={self.gitlab_default_branch}"
            )
        file_data, err = json_fetch(versions_url)

        if err:
            raise err

        if file_data:
            return json.loads(
                codecs.decode(
                    file_data["content"].encode(),
                    file_data["encoding"]
                )
            )

        return []

    def get_commit(self, branch_name: str) -> Commit:
        # GitHub and GitLab supports accessing commits via other references like branch names
        # Gitea/Codeberg only supports commit hashes so we have to use the branches API
        api = "commits" if self.host == "github.com" else "branches"
        url = f"{self.host_api}/repos/{self.user}/{self.repo}/{api}/{branch_name}"
        if self.host == "gitlab.com":
            url = f"{self.host_api}/projects/{self.gitlab_project_id}/repository/commits/{branch_name}"

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

    def find_compatible_version(self) -> Commit:
        """
        Finds first version that is compatible with users Ulauncher version.
        Returns a commit or branch/tag name and datetime.
        """

        versions = None

        try:
            versions = self.get_versions()
            self.validate_versions(versions)
            branch_name = next(
                (v['commit'] for v in versions if satisfies(API_VERSION, v['required_api_version'])),
                None
            )

            if not branch_name:
                raise ExtensionRemoteError(
                    f"This extension is not compatible with your Ulauncher API version (v{API_VERSION})",
                    ExtensionError.Incompatible
                )

            return self.get_commit(branch_name)
        except URLError as e:
            if not versions:
                raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from e
            if getattr(e, "code") == 404:
                message = f'Invalid branch "{branch_name}" in version declaration.'
                raise ExtensionRemoteError(message, ExtensionError.InvalidVersionDeclaration) from e
            message = f'Could not fetch repository "{branch_name}".'
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
