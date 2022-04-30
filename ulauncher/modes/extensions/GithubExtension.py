import re
import json
import logging
from datetime import datetime
from urllib.request import urlopen
from urllib.error import HTTPError
from typing import Dict, List, cast

from ulauncher.config import API_VERSION
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.date import iso_to_datetime
from ulauncher.utils.version import satisfies, valid_range
from ulauncher.api.shared.errors import ExtensionError, UlauncherAPIError

DEFAULT_GITHUB_BRANCH = 'master'

logger = logging.getLogger(__name__)

ManifestPreference = TypedDict('ManifestPreference', {
    'default_value': str,
    'id': str,
    'name': str,
    'type': str
})

ManifestOptions = TypedDict('ManifestOptions', {
    'query_debounce': float
})

Manifest = TypedDict('Manifest', {
    'required_api_version': str,
    'description': str,
    'developer_name': str,
    'icon': str,
    'name': str,
    'options': ManifestOptions,
    'preferences': List[ManifestPreference]
})

Commit = TypedDict('Commit', {
    'sha': str,
    'time': datetime
})


class GithubExtensionError(UlauncherAPIError):
    pass


class GithubExtension:

    url_match_pattern = r'^(https:\/\/github.com\/|git@github.com:)(([\w-]+\/[\w-]+))\/?(.git|tree\/master\/?)?$'
    url_file_template = 'https://raw.githubusercontent.com/{project_path}/{branch}/{file_path}'
    url_commit_template = 'https://api.github.com/repos/{project_path}/commits/{commit}'

    def __init__(self, url):
        self.url = url

    def validate_url(self):
        if not re.match(self.url_match_pattern, self.url, re.I):
            raise GithubExtensionError(f'Invalid Extension url: {self.url}', ExtensionError.InvalidUrl)

    def find_compatible_version(self) -> Commit:
        """
        Finds maximum version that is compatible with current version of Ulauncher
        and returns a commit or branch/tag name

        :raises ulauncher.modes.extensions.GithubExtension.InvalidVersionDeclaration:
        """
        sha_or_branch = ""
        for ver in self.read_versions():
            if satisfies(API_VERSION, ver['required_api_version']):
                sha_or_branch = ver['commit']

        if not sha_or_branch:
            raise GithubExtensionError(
                f"This extension is not compatible with current version Ulauncher extension API (v{API_VERSION})",
                ExtensionError.Incompatible)

        try:
            return self.get_commit(sha_or_branch)
        except HTTPError as e:
            raise GithubExtensionError(
                f'Branch/commit "{sha_or_branch}" does not exist.',
                ExtensionError.InvalidVersionDeclaration
            ) from e

    def get_commit(self, sha_or_branch) -> Commit:
        """
        Github response example: https://api.github.com/repos/Ulauncher/Ulauncher/commits/a1304f5a
        """

        project_path = self._get_project_path()
        url = self.url_commit_template.format(project_path=project_path, commit=sha_or_branch)
        resp = json.loads(urlopen(url).read().decode('utf-8'))

        return {
            'sha': resp['sha'],
            'time': iso_to_datetime(resp['commit']['committer']['date'])
        }

    def _read_json(self, commit, file_path) -> Dict:
        project_path = self._get_project_path()
        url = self.url_file_template.format(project_path=project_path, branch=commit, file_path=file_path)

        try:
            return json.loads(urlopen(url).read().decode('utf-8'))
        except HTTPError as e:
            logger.warning('_read_json("%s", "%s") failed. %s: %s', commit, file_path, type(e).__name__, e)
            if e.code == 404:
                raise GithubExtensionError(
                    f'Could not find versions.json file using URL "{url}"',
                    ExtensionError.MissingVersionDeclaration
                ) from e
            raise GithubExtensionError(
                f'Could not read versions.json file using URL "{url}"',
                ExtensionError.InvalidVersionDeclaration
            ) from e

    def read_versions(self) -> List[Dict[str, str]]:
        versions = self._read_json('master', 'versions.json')

        if not isinstance(versions, list):
            raise GithubExtensionError(
                'versions.json should contain a list',
                ExtensionError.InvalidVersionDeclaration
            )
        for ver in versions:
            if not isinstance(ver, dict):
                raise GithubExtensionError(
                    'versions.json should contain a list of objects',
                    ExtensionError.InvalidVersionDeclaration
                )
            if not isinstance(ver.get('required_api_version'), str):
                raise GithubExtensionError(
                    'versions.json: required_api_version should be a string',
                    ExtensionError.InvalidVersionDeclaration
                )
            if not isinstance(ver.get('commit'), str):
                raise GithubExtensionError(
                    'versions.json: commit should be a string',
                    ExtensionError.InvalidVersionDeclaration
                )

            valid = False
            try:
                valid = valid_range(ver['required_api_version'])
            # pylint: disable=broad-except
            except Exception:
                pass
            if not valid:
                raise GithubExtensionError(
                    f"versions.json: invalid range '{ver['required_api_version']}'",
                    ExtensionError.InvalidVersionDeclaration
                )

        return versions

    def read_manifest(self, commit) -> Manifest:
        return cast(Manifest, self._read_json(commit, 'manifest.json'))

    def get_download_url(self, commit: str = DEFAULT_GITHUB_BRANCH) -> str:
        """
        >>> Ulauncher/ulauncher-timer
        <<< https://github.com/Ulauncher/ulauncher-timer/tarball/master
        """
        return f'https://github.com/{self._get_project_path()}/tarball/{commit}'

    def get_ext_id(self) -> str:
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< com.github.ulauncher.ulauncher-timer
        """
        return f"com.github.{self._get_project_path().replace('/', '.').lower()}"

    def _get_project_path(self) -> str:
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< Ulauncher/ulauncher-timer
        """
        match = re.match(self.url_match_pattern, self.url, re.I)
        if not match:
            raise GithubExtensionError(f'Invalid Extension url: {self.url}', ExtensionError.InvalidUrl)

        return match.group(2)
