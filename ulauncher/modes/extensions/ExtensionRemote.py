import codecs
import json
import re
import logging
from datetime import datetime
from urllib.request import urlopen
from typing import Optional, Tuple

from ulauncher.config import API_VERSION
from ulauncher.utils.version import satisfies
from ulauncher.api.shared.errors import ExtensionError, UlauncherAPIError
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest

logger = logging.getLogger()

Commit = Tuple[str, str]


class ExtensionRemoteError(UlauncherAPIError):
    pass


def json_fetch(url):
    try:
        return json.loads(urlopen(url).read())
    except Exception as e:
        # If json.loads fails, treat it as a network error too.
        # It should never happen as all these API endpoint are exclusively JSON
        err_msg = f'Could not access repository resource "{url}"'
        raise ExtensionRemoteError(err_msg, ExtensionError.Network) from e


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
            projects = json_fetch(f"{host_api}/users/{self.user}/projects?search={self.repo}")
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

        file_data = json_fetch(file_api_url)

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

        try:
            tags_data = json_fetch(tags_url)

            for tag in tags_data or []:
                if tag["name"].startswith("apiv") and satisfies(API_VERSION, tag["name"][4:]):
                    commit = tag["commit"]
                    verion = tag["name"][4:]
                    id = commit.get("sha", commit["id"])  # id fallback is needed for GitLab
                    commit_time = commit.get("created", commit.get("created_at"))
                    tags[verion] = (id, commit_time)

            if tags:
                id, commit_time = tags[max(tags)]
                if id and self.host == "github.com":  # GitHub's tag API doesn't give any dates
                    commit_data = json_fetch(f"{self.host_api}/repos/{self.user}/{self.repo}/commits/{id}")
                    commit_time = commit_data["commiter"]["date"]
                if id and commit_time:
                    date = datetime.strptime(commit_time, self.date_format)
                    return id, date.isoformat()

        except Exception as e:
            logger.warning("Unexpected error retrieving version from tags '%s' (%s: %s)", self.url, type(e).__name__, e)

        return None

    def get_commit(self, ref: str = "HEAD") -> Commit:
        if self.host == "gitlab.com":
            url = f"{self.host_api}/commits/{ref}"
        elif self.host == "github.com":
            url = f"{self.host_api}/repos/{self.user}/{self.repo}/commits/{ref}"
        else:
            # Gitea/Codeberg API differs from GitHub here, but has the same API
            url = f"{self.host_api}/repos/{self.user}/{self.repo}/git/commits/{ref}"

        try:
            response = json_fetch(url)
            id = response.get("sha") or response.get("id")
            commit_time = response.get("created_at") or response["commit"]["committer"]["date"]
            date = datetime.strptime(commit_time, self.date_format)
            return id, date.isoformat()
        except (KeyError, TypeError) as e:
            err_msg = f'Could not fetch reference "{ref}" for {self.url}.'
            raise ExtensionRemoteError(err_msg, ExtensionError.Other) from e

    def get_latest_compatible_commit(self) -> Commit:
        """
        Finds first version that is compatible with users Ulauncher version.
        Returns a commit hash and datetime.
        """
        manifest = ExtensionManifest(json.loads(self.fetch_file("manifest.json") or "{}"))

        if satisfies(API_VERSION, manifest.api_version):
            return self.get_commit()

        tag = self.get_compatible_commit_from_tags()
        if tag:
            return tag

        if satisfies("2.0", manifest.api_version):
            logger.warning("Falling back on using API 2.0 version for %s.", self.repo)
            return self.get_commit()

        message = f"{manifest.name} does not support Ulauncher API v{API_VERSION}."
        raise ExtensionRemoteError(message, ExtensionError.Incompatible)
