import os
import re
import json
from urllib2 import urlopen
from zipfile import ZipFile
from urllib import urlretrieve
from tempfile import mktemp
from shutil import rmtree
from time import time

from ulauncher.config import CONFIG_DIR, EXTENSIONS_DIR
from ulauncher.util.decorator.singleton import singleton
from .ExtensionsDb import ExtensionsDb
from .ExtensionRunner import ExtensionRunner, ExtensionIsNotRunningError


DEFAULT_GITHUB_BRANCH = 'master'


class ExtensionDownloader(object):

    @classmethod
    @singleton
    def get_instance(cls):
        ext_db = ExtensionsDb.get_instance()
        ext_runner = ExtensionRunner.get_instance()
        return cls(ext_db, ext_runner)

    def __init__(self, ext_db, ext_runner):
        super(ExtensionDownloader, self).__init__()
        self.ext_db = ext_db
        self.ext_runner = ext_runner

    def download(self, url):
        """
        1. check if ext already exists
        2. get last commit info
        3. download & unzip
        4. add to the db
        5. start the ext

        :rtype: str
        :returns: Extension ID
        :raises AlreadyDownloadedError:
        :raises InvalidGithubUrlError:
        """
        ext_id = 'com.github.%s' % get_project_path(url).replace('/', '.').lower()
        if self.ext_db.find(ext_id):
            raise AlreadyDownloadedError('Extension with given URL is already added')

        try:
            ext_meta = get_ext_meta(url)
        except Exception as e:
            raise InvalidGithubUrlError('Project not available on Github')

        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)

        filename = download_zip(url)
        unzip(filename, ext_path)
        self.ext_db.put(ext_id, {
            'id': ext_id,
            'url': url,
            'updated_at': time(),
            'last_commit': ext_meta['last_commit'],
            'last_commit_time_iso': ext_meta['last_commit_time_iso']
        })
        self.ext_db.commit()

        return ext_id

    def remove(self, ext_id):
        try:
            self.ext_runner.stop(ext_id)
        except ExtensionIsNotRunningError:
            pass
        self.ext_db.remove(ext_id)
        self.ext_db.commit()

    def update(self, ext_id):
        """
        :raises ExtensionNotFound:
        :rtype: boolean
        :returns: False if already up-to-date, True if was updated
        """
        ext_info = self.ext_db.find(ext_id)
        if not ext_info:
            raise ExtensionNotFound("Extension not found")

        url = ext_info['url']

        try:
            ext_meta = get_ext_meta(url)
        except Exception as e:
            raise InvalidGithubUrlError('Project not available on Github')

        if ext_info['last_commit'] == ext_meta['last_commit']:
            return False

        need_restart = self.ext_runner.is_running(ext_id)
        if need_restart:
            self.ext_runner.stop(ext_id)

        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)

        filename = download_zip(url)
        unzip(filename, ext_path)
        ext_info['updated_at'] = time()
        ext_info['last_commit'] = ext_meta['last_commit']
        ext_info['last_commit_time_iso'] = ext_meta['last_commit_time_iso']
        self.ext_db.put(ext_id, ext_info)
        self.ext_db.commit()

        if need_restart:
            self.ext_runner.run(ext_id)

        return True


def get_ext_meta(url):
    """
    :raises urllib2.HTTPError:
    """
    project_path = get_project_path(url)
    branch_head_url = 'https://api.github.com/repos/%s/git/refs/heads/%s' % (project_path, DEFAULT_GITHUB_BRANCH)
    branch_head = json.load(urlopen(branch_head_url))
    branch_head_commit = json.load(urlopen(branch_head['object']['url']))

    return {
        'last_commit': branch_head_commit['sha'],
        'last_commit_time_iso': branch_head_commit['committer']['date']
    }


def unzip(filename, ext_path):
    with ZipFile(filename) as zipfile:
        zipfile.extractall(ext_path)

    if os.path.exists(ext_path):
        rmtree(ext_path)
    os.mkdir(ext_path)


def download_zip(url):
    url = get_zip_url(url)
    dest_zip = mktemp('.zip')
    filename, _ = urllib.urlretrieve(url, dest_zip)

    return filename


def get_zip_url(url):
    """
    >>> https://github.com/Ulauncher/ulauncher-timer
    <<< https://github.com/Ulauncher/ulauncher-timer/archive/master.zip
    """
    return '%s/archive/%s.zip' % (url, DEFAULT_GITHUB_BRANCH)


def get_project_path(github_url):
    match = re.match(r'^http(s)?:\/\/github.com\/([\w-]+\/[\w-]+)(\/)?$',
                     github_url, re.I)
    if not match:
        raise InvalidGithubUrlError('Invalid GithubUrl: %s' % github_url)

    return match.group(2)


class ExtensionDownloaderError(Exception):
    pass


class ExtensionNotFound(ExtensionDownloaderError):
    pass


class AlreadyDownloadedError(ExtensionDownloaderError):
    pass


class InvalidGithubUrlError(ExtensionDownloaderError):
    pass
