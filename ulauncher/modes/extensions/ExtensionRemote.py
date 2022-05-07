import codecs
import json
import re
import logging
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from typing import Optional, Tuple

from ulauncher.config import API_VERSION
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
    date_format = '%Y-%m-%dT%H:%M:%S%z'

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
            self.date_format = '%Y-%m-%dT%H:%M:%SZ'
        elif self.host == "gitlab.com":
            host_api = "https://gitlab.com/api/v4"
            projects, err = json_fetch(f"{host_api}/users/{self.user}/projects?search={self.repo}")
            if err:
                raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from err
            project = next((p for p in projects if p["name"] == self.repo), None)

            self.host_api = f"{host_api}/projects/{project['id']}/repository"
            self.date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        else:
            self.host_api = f"https://{self.host}/api/v1"

    def get_download_url(self, commit: str) -> str:
        if self.host == "gitlab.com":
            return f'https://{self.host}/{self.user}/{self.repo}/-/archive/{commit}/{self.repo}-{commit}.tar.gz'
        return f'https://{self.host}/{self.user}/{self.repo}/archive/{commit}.tar.gz'

    def fetch_file(self, file_path) -> Optional[str]:
        # This saves us a request compared to using the "raw" file API that needs to know the branch
        file_api_url = f"{self.host_api}/repos/{self.user}/{self.repo}/contents/{file_path}"
        if self.host == "gitlab.com":
            file_api_url = f"{self.host_api}/files/{file_path}?ref=HEAD"
        file_data, err = json_fetch(file_api_url)

        if err:
            raise err

        if file_data and file_data.get("content") and file_data.get("encoding"):
            return codecs.decode(file_data["content"].encode(), file_data["encoding"]).decode()

        return None

    def get_compatible_commit_from_tags(self) -> Optional[Commit]:
        """
        This method is new for v6, but intentionally undocumented because we still want extension
        devs to use the old way until Ulauncher 5/apiv2 is fully phased out
        """
        tags = {}
        # pagination is only implemented for GitHub (default 30, max 100)
        tags_url = f"{self.host_api}/repos/{self.user}/{self.repo}/tags?per_page=100"
        if self.host == "gitlab.com":
            # GitLab's API allows to filter out tags starting with our prefix
            tags_url = f"{self.host_api}/tags?search=^apiv"
        tags_data, _ = json_fetch(tags_url)

        try:
            for tag in tags_data or []:
                if tag["name"].startswith("apiv") and satisfies(API_VERSION, tag["name"][4:]):
                    commit = tag["commit"]
                    verion = tag["name"][4:]
                    id = commit.get("sha", commit["id"])  # id fallback is needed for GitLab
                    commit_time = commit.get("created", commit.get("created_at"))
                    tags[verion] = (id, commit_time)
        except (KeyError, TypeError):
            pass

        if tags:
            id, commit_time = tags[max(tags)]
            if id and self.host == "github.com":  # GitHub's tag API doesn't give any dates
                commit_data, _ = json_fetch(f"{self.host_api}/repos/{self.user}/{self.repo}/commits/{id}")
                commit_time = commit_data["commiter"]["date"]
            if id and commit_time:
                return id, datetime.strptime(commit_time, self.date_format)

        return None

    def get_compatible_commit_from_versions_json(self) -> Optional[Commit]:
        # This saves us a request compared to using the "raw" file API that needs to know the branch
        versions = json.loads(self.fetch_file("versions.json") or "[]")
        self.validate_versions(versions)

        versions_filter = (v['commit'] for v in versions if satisfies(API_VERSION, v['required_api_version']))
        ref = next(versions_filter, None)
        return self.get_commit(ref) if ref else None

    def get_commit(self, ref: str = "HEAD") -> Commit:
        if self.host == "gitlab.com":
            url = f"{self.host_api}/commits/{ref}"
        elif self.host == "github.com":
            url = f"{self.host_api}/repos/{self.user}/{self.repo}/commits/{ref}"
        else:
            # Gitea/Codeberg API differs from GitHub here, but has the same API
            url = f"{self.host_api}/repos/{self.user}/{self.repo}/git/commits/{ref}"

        response, err = json_fetch(url)

        if err:
            if getattr(err, "code") == 404:
                message = f'Invalid reference "{ref}" in version declaration.'
                raise ExtensionRemoteError(message, ExtensionError.InvalidVersionDeclaration) from err
            raise ExtensionRemoteError(f'Could not fetch reference "{ref}".', ExtensionError.Network) from err

        try:
            id = response.get("sha") or response.get("id")
            commit_time = response.get("created_at") or response["commit"]["committer"]["date"]
            return id, datetime.strptime(commit_time, self.date_format)
        except (KeyError, TypeError):
            pass

        raise ExtensionRemoteError(
            f'Invalid metadata for commit url "{url}"',
            ExtensionError.InvalidVersionDeclaration
        )

    def get_latest_compatible_commit(self) -> Commit:
        """
        Finds first version that is compatible with users Ulauncher version.
        Returns a commit hash and datetime.
        """
        try:
            manifest = json.loads(self.fetch_file("manifest.json") or "{}")
        except URLError as e:
            raise ExtensionRemoteError("Could not access repository", ExtensionError.Network) from e

        if satisfies(API_VERSION, manifest.get("required_api_version")):
            return self.get_commit("HEAD")

        commit = self.get_compatible_commit_from_tags() or self.get_compatible_commit_from_versions_json()
        if not commit:
            message = f"This extension is not compatible with your Ulauncher API version (v{API_VERSION})."
            raise ExtensionRemoteError(message, ExtensionError.Incompatible)

        return commit

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
