import re
import json
from typing import Dict, List
from urllib.request import urlopen

from ulauncher.api.version import api_version
from ulauncher.util.semver import satisfies, valid_range
from ulauncher.util.named_tuple_from_dict import namedtuple_from_dict

DEFAULT_GITHUB_BRANCH = 'master'

# pylint: disable=too-few-public-methods
class IPreference:
    default_value = None  # type: str
    id = None  # type: str
    name = None  # type: str
    type = None  # type: str


class IOptions:
    query_debounce = None  # type: float


class IManifest:
    required_api_version = None  # type: str
    description = None  # type: str
    developer_name = None  # type: str
    icon = None  # type: str
    name = None  # type: str
    options = None  # type: IOptions
    preferences = None  # type: List[IPreference]


class ICommit:
    last_commit = None  # type: str
    last_commit_time = None  # type: str


class GithubExtension:

    url_match_pattern = r'^https:\/\/github.com\/([\w-]+\/[\w-]+)$'
    url_file_template = 'https://raw.githubusercontent.com/{project_path}/{branch}/{file_path}'

    def __init__(self, url):
        self.url = url

    def validate_url(self):
        if not re.match(self.url_match_pattern, self.url, re.I):
            raise InvalidGithubUrlError('Invalid GithubUrl: %s' % self.url)

    def find_compatible_version(self) -> str:
        """
        Finds maximum version that is compatible with current version of Ulauncher
        and returns a commit or branch/tag name
        """
        commit = ""
        for ver in self.read_versions():
            if satisfies(api_version, ver['required_api_version']):
                commit = ver['commit']

        if not commit:
            raise InvalidVersionsFileError(
                "This extension is not compatible with current version Ulauncher extension API (v%s)" % api_version)

        return commit

    def _read_json(self, commit, file_path) -> Dict:
        project_path = self._get_project_path()
        url = self.url_file_template.format(project_path=project_path, branch=commit, file_path=file_path)
        return json.loads(urlopen(url).read().decode('utf-8'))

    def read_versions(self) -> List[Dict[str, str]]:
        versions = self._read_json('master', 'versions.json')
        if not isinstance(versions, list):
            raise InvalidVersionsFileError('versions.json should contain a list')
        for ver in versions:
            if not isinstance(ver, dict):
                raise InvalidVersionsFileError('versions.json should contain a list of objects')
            if not isinstance(ver.get('required_api_version'), str):
                raise InvalidVersionsFileError('versions.json: required_api_version should be a string')
            if not isinstance(ver.get('commit'), str):
                raise InvalidVersionsFileError('versions.json: commit should be a string')

            valid = False
            try:
                valid = valid_range(ver['required_api_version'], False)
            # pylint: disable=broad-except
            except Exception:
                pass
            if not valid:
                raise InvalidVersionsFileError("versions.json: invalid range '%s'" % ver['required_api_version'])

        return versions

    def read_manifest(self, commit) -> IManifest:
        return namedtuple_from_dict(self._read_json(commit, 'manifest.json'))

    def get_last_commit(self) -> ICommit:
        """
        :rtype dict: {'last_commit': str, 'last_commit_time': str}
        :raises urllib.error.HTTPError:
        """
        project_path = self._get_project_path()
        branch_head_url = 'https://api.github.com/repos/%s/git/refs/heads/%s' % (project_path, DEFAULT_GITHUB_BRANCH)
        branch_head = json.loads(urlopen(branch_head_url).read().decode('utf-8'))
        branch_head_commit = json.loads(urlopen(branch_head['object']['url']).read().decode('utf-8'))

        return namedtuple_from_dict({
            'last_commit': branch_head_commit['sha'],
            'last_commit_time': branch_head_commit['committer']['date']  # ISO date
        })

    def get_download_url(self, commit=DEFAULT_GITHUB_BRANCH) -> str:
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< https://github.com/Ulauncher/ulauncher-timer/archive/master.zip
        """
        return '%s/archive/%s.zip' % (self.url, commit)

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
            raise InvalidGithubUrlError('Invalid GithubUrl: %s' % self.url)

        return match.group(1)


class InvalidGithubUrlError(Exception):
    pass


class InvalidVersionsFileError(Exception):
    pass
