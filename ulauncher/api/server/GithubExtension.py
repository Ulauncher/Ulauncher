import re
import json
import logging
from datetime import datetime
from urllib.request import urlopen
from typing import Dict, List, cast
from ulauncher.utils.mypy_extensions import TypedDict

from ulauncher.utils.date import iso_to_datetime
from ulauncher.api.version import api_version
from ulauncher.api.shared.errors import ErrorName, UlauncherAPIError
from ulauncher.utils.semver import satisfies, valid_range

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

    def _unsafe_fetch_json(self, url):
        return json.loads(urlopen(url).read().decode('utf-8'))

    def validate_url(self):
        if not re.match(self.url_match_pattern, self.url, re.I):
            raise GithubExtensionError('Invalid GithubUrl: %s' % self.url, ErrorName.InvalidGithubUrl)

    def find_compatible_version(self) -> Commit:
        """
        Finds latest version that is compatible with current version of Ulauncher
        and returns a commit or branch/tag name

        :raises ulauncher.api.server.GithubExtension.InvalidVersionsFileError:
        """
        sha_or_branch = ""
        for ver in self.read_versions():
            if satisfies(api_version, ver['required_api_version']):
                sha_or_branch = ver['commit']

        if not sha_or_branch:
            raise GithubExtensionError(
                "This extension is not compatible with current version Ulauncher extension API (v%s)" % api_version,
                ErrorName.IncompatibleVersion)

        return self.get_commit(sha_or_branch)

    def get_commit(self, sha_or_branch) -> Commit:
        """
        Github response example: https://api.github.com/repos/Ulauncher/Ulauncher/commits/a1304f5a
        """

        project_path = self._get_project_path()
        url = self.url_commit_template.format(project_path=project_path, commit=sha_or_branch)

        try:
            resp = self._unsafe_fetch_json(url)
        except Exception as e:
            raise GithubExtensionError(
                f'Commit/branch "{sha_or_branch}" does not exist or could not be retrieved.',
                ErrorName.InvalidVersionsJson
            ) from e

        return {
            'sha': resp['sha'],
            'time': iso_to_datetime(resp['commit']['committer']['date'])
        }

    def _read_json(self, commit, file_path) -> Dict:
        project_path = self._get_project_path()
        url = self.url_file_template.format(project_path=project_path, branch=commit, file_path=file_path)

        try:
            return self._unsafe_fetch_json(url)
        except Exception as e:
            if getattr(e, 'code', None) == 404:
                raise GithubExtensionError('Could not find versions.json file using URL "%s"' %
                                           url, ErrorName.IncompatibleVersion) from e
            raise GithubExtensionError('Unexpected Github API Error', ErrorName.GithubApiError) from e

    def read_versions(self) -> List[Dict[str, str]]:
        versions = self._read_json('HEAD', 'versions.json')

        if not isinstance(versions, list):
            raise GithubExtensionError('versions.json should contain a list', ErrorName.InvalidVersionsJson)
        for ver in versions:
            if not isinstance(ver, dict):
                raise GithubExtensionError('versions.json should contain a list of objects',
                                           ErrorName.InvalidVersionsJson)
            if not isinstance(ver.get('required_api_version'), str):
                raise GithubExtensionError(
                    'versions.json: required_api_version should be a string', ErrorName.InvalidVersionsJson)
            if not isinstance(ver.get('commit'), str):
                raise GithubExtensionError('versions.json: commit should be a string', ErrorName.InvalidVersionsJson)

            valid = False
            try:
                valid = valid_range(ver['required_api_version'], False)
            # pylint: disable=broad-except
            except Exception:
                pass
            if not valid:
                raise GithubExtensionError("versions.json: invalid range '%s'" % ver['required_api_version'],
                                           ErrorName.InvalidVersionsJson)

        return versions

    def read_manifest(self, commit) -> Manifest:
        return cast(Manifest, self._read_json(commit, 'manifest.json'))

    def get_download_url(self, commit="HEAD") -> str:
        """
        >>> Ulauncher/ulauncher-timer
        <<< https://github.com/Ulauncher/ulauncher-timer/tarball/master
        """
        return 'https://github.com/%s/tarball/%s' % (self._get_project_path(), commit)

    def get_ext_id(self) -> str:
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< com.github.ulauncher.ulauncher-timer
        """
        return 'com.github.%s' % self._get_project_path().replace('/', '.').lower()

    def _get_project_path(self) -> str:
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< Ulauncher/ulauncher-timer
        """
        match = re.match(self.url_match_pattern, self.url, re.I)
        if not match:
            raise GithubExtensionError('Invalid GithubUrl: %s' % self.url, ErrorName.InvalidGithubUrl)

        return match.group(2)
