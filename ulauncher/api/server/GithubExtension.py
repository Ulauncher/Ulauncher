import re
import json
import logging
from urllib2 import urlopen, HTTPError

from ulauncher.util.date import iso_to_datetime
from ulauncher.api.version import api_version
from ulauncher.util.semver import satisfies, valid_range

DEFAULT_GITHUB_BRANCH = 'master'

logger = logging.getLogger(__name__)


class GithubExtension(object):

    url_match_pattern = r'^https:\/\/github.com\/([\w-]+\/[\w-]+)$'
    url_file_template = 'https://raw.githubusercontent.com/{project_path}/{branch}/{file_path}'
    url_commit_template = 'https://api.github.com/repos/{project_path}/commits/{commit}'

    def __init__(self, url):
        self.url = url

    def validate_url(self):
        if not re.match(self.url_match_pattern, self.url, re.I):
            raise GithubExtensionError('Invalid GithubUrl: %s' % self.url)

    def find_compatible_version(self):
        """
        Finds maximum version that is compatible with current version of Ulauncher
        and returns a commit or branch/tag name

        :raises ulauncher.api.server.GithubExtension.InvalidVersionsFileError:
        """
        sha_or_branch = ""
        try:
            versions = self.read_versions()
        except VersionsJsonNotFoundError:
            # this must be an extension that only supports API v1
            return self.get_commit('master')

        for ver in versions:
            if satisfies(api_version, ver['required_api_version']):
                sha_or_branch = ver['commit']

        if not sha_or_branch:
            raise GithubExtensionError(
                "This extension is not compatible with current version Ulauncher extension API (v%s)" % api_version)

        return self.get_commit(sha_or_branch)

    def get_commit(self, sha_or_branch):
        """
        Github response example: https://api.github.com/repos/Ulauncher/Ulauncher/commits/a1304f5a
        """

        project_path = self._get_project_path()
        url = self.url_commit_template.format(project_path=project_path, commit=sha_or_branch)
        resp = json.load(urlopen(url))

        return {
            'sha': resp['sha'],
            'time': iso_to_datetime(resp['commit']['committer']['date'])
        }

    def _read_json(self, commit, file_path):
        project_path = self._get_project_path()
        url = self.url_file_template.format(project_path=project_path, branch=commit, file_path=file_path)

        try:
            return json.load(urlopen(url))
        except HTTPError as e:
            if e.code == 404:
                raise GithubFileNotFoundError('Could not find %s using URL "%s"' % (file_path, url))
            logger.exception('_read_json("%s", "%s") failed. %s: %s', commit, file_path, type(e).__name__, e)
            raise GithubExtensionError('Unexpected Github API Error. Please try again later')

    def read_versions(self):
        try:
            versions = self._read_json('master', 'versions.json')
        except GithubFileNotFoundError:
            raise VersionsJsonNotFoundError('version.json was not found in repository %s' % self.url)

        if not isinstance(versions, list):
            raise GithubExtensionError('versions.json should contain a list')
        for ver in versions:
            if not isinstance(ver, dict):
                raise GithubExtensionError('versions.json should contain a list of objects')
            if not isinstance(ver.get('required_api_version'), basestring):
                raise GithubExtensionError(
                    'versions.json: required_api_version should be a string')
            if not isinstance(ver.get('commit'), basestring):
                raise GithubExtensionError('versions.json: commit should be a string')

            valid = False
            try:
                valid = valid_range(ver['required_api_version'], False)
            except Exception:
                pass
            if not valid:
                raise GithubExtensionError("versions.json: invalid range '%s'" % ver['required_api_version'])

        return versions

    def read_manifest(self, commit):
        return self._read_json(commit, 'manifest.json')

    def get_download_url(self, commit=DEFAULT_GITHUB_BRANCH):
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< https://github.com/Ulauncher/ulauncher-timer/archive/master.zip
        """
        return '%s/archive/%s.zip' % (self.url, commit)

    def get_ext_id(self):
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< com.github.ulauncher.ulauncher-timer
        """
        return 'com.github.%s' % self._get_project_path().replace('/', '.').lower()

    def _get_project_path(self):
        """
        >>> https://github.com/Ulauncher/ulauncher-timer
        <<< Ulauncher/ulauncher-timer
        """
        match = re.match(self.url_match_pattern, self.url, re.I)
        if not match:
            raise GithubExtensionError('Invalid GithubUrl: %s' % self.url)

        return match.group(1)


class GithubExtensionError(Exception):
    pass


class GithubFileNotFoundError(GithubExtensionError):
    pass


class VersionsJsonNotFoundError(GithubFileNotFoundError):
    pass
