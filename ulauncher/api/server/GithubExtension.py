import re
import json
from urllib2 import urlopen

DEFAULT_GITHUB_BRANCH = 'master'


class GithubExtension:

    url_match_pattern = r'^https:\/\/github.com\/([\w-]+\/[\w-]+)$'

    def __init__(self, url):
        self.url = url

    def validate_url(self):
        if not re.match(self.url_match_pattern, self.url, re.I):
            raise InvalidGithubUrlError('Invalid GithubUrl: %s' % self.url)

    def get_last_commit(self):
        """
        :rtype dict: {'last_commit': str, 'last_commit_time': str}
        :raises urllib2.HTTPError:
        """
        project_path = self._get_project_path()
        branch_head_url = 'https://api.github.com/repos/%s/git/refs/heads/%s' % (project_path, DEFAULT_GITHUB_BRANCH)
        branch_head = json.load(urlopen(branch_head_url))
        branch_head_commit = json.load(urlopen(branch_head['object']['url']))

        return {
            'last_commit': branch_head_commit['sha'],
            'last_commit_time': branch_head_commit['committer']['date']  # ISO date
        }

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
            raise InvalidGithubUrlError('Invalid GithubUrl: %s' % self.url)

        return match.group(1)


class InvalidGithubUrlError(Exception):
    pass
