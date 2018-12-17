import os
import logging
from zipfile import ZipFile
from urllib.request import urlretrieve
from tempfile import mktemp, mkdtemp
from shutil import rmtree, move
from datetime import datetime

from ulauncher.config import EXTENSIONS_DIR
from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton
from ulauncher.api.server.ExtensionDb import ExtensionDb
from ulauncher.api.server.GithubExtension import GithubExtension, InvalidGithubUrlError
from ulauncher.api.server.ExtensionRunner import ExtensionRunner, ExtensionIsNotRunningError
from ulauncher.api.server.extension_finder import find_extensions


logger = logging.getLogger(__name__)


class ExtensionDownloader:

    @classmethod
    @singleton
    def get_instance(cls) -> 'ExtensionDownloader':
        ext_db = ExtensionDb.get_instance()
        ext_runner = ExtensionRunner.get_instance()
        return cls(ext_db, ext_runner)

    def __init__(self, ext_db: ExtensionDb, ext_runner: ExtensionRunner):
        super(ExtensionDownloader, self).__init__()
        self.ext_db = ext_db
        self.ext_runner = ext_runner

    def download(self, url: str) -> str:
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
        gh_ext = GithubExtension(url)
        gh_ext.validate_url()

        ext_id = gh_ext.get_ext_id()
        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)
        if os.path.exists(ext_path):
            raise AlreadyDownloadedError('Extension with given URL is already added')

        try:
            gh_commit = gh_ext.get_last_commit()
        except Exception as e:
            logger.exception('ext_downloader.download() failed. %s: %s', type(e).__name__, e)
            raise InvalidGithubUrlError('Project is not available on Github')

        filename = download_zip(gh_ext.get_download_url(gh_commit['last_commit']))
        unzip(filename, ext_path)

        self.ext_db.put(ext_id, {
            'id': ext_id,
            'url': url,
            'updated_at': datetime.now().isoformat(),
            'last_commit': gh_commit['last_commit'],
            'last_commit_time': gh_commit['last_commit_time']
        })
        self.ext_db.commit()

        return ext_id

    @run_async(daemon=True)
    def download_missing(self) -> None:
        already_downloaded = {id for id, _ in find_extensions(EXTENSIONS_DIR)}
        for id, ext in self.ext_db.get_records().items():
            if id in already_downloaded:
                continue

            logger.info('Downloading missing extension %s', id)
            try:
                ext_id = self.download(ext['url'])
                self.ext_runner.run(ext_id)
            # pylint: disable=broad-except
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)

    def remove(self, ext_id: str) -> None:
        try:
            self.ext_runner.stop(ext_id)
        except ExtensionIsNotRunningError:
            pass

        rmtree(os.path.join(EXTENSIONS_DIR, ext_id))
        self.ext_db.remove(ext_id)
        self.ext_db.commit()

    def update(self, ext_id: str) -> bool:
        """
        :raises ExtensionNotFound:
        :rtype: boolean
        :returns: False if already up-to-date, True if was updated
        """
        ext = self.ext_db.find(ext_id)
        if not ext:
            raise ExtensionNotFound("Extension not found")

        url = ext['url']
        gh_ext = GithubExtension(url)

        try:
            gh_commit = self.get_new_version(ext_id)
        except ExtensionIsUpToDateError:
            return False

        need_restart = self.ext_runner.is_running(ext_id)
        if need_restart:
            self.ext_runner.stop(ext_id)

        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)

        filename = download_zip(gh_ext.get_download_url(gh_commit['last_commit']))
        unzip(filename, ext_path)
        ext['updated_at'] = datetime.now().isoformat()
        ext['last_commit'] = gh_commit['last_commit']
        ext['last_commit_time'] = gh_commit['last_commit_time']
        self.ext_db.put(ext_id, ext)
        self.ext_db.commit()

        if need_restart:
            self.ext_runner.run(ext_id)

        return True

    def get_new_version(self, ext_id: str) -> dict:
        """
        Returns dict with commit info about a new version or raises ExtensionIsUpToDateError
        """
        ext = self.ext_db.find(ext_id)
        if not ext:
            raise ExtensionNotFound("Extension %s not found" % ext_id)

        url = ext['url']
        gh_ext = GithubExtension(url)

        try:
            gh_commit = gh_ext.get_last_commit()
        except Exception as e:
            logger.error('gh_ext.get_ext_meta() failed. %s: %s', type(e).__name__, e)
            raise InvalidGithubUrlError('Project is not available on Github')

        if ext['last_commit'] == gh_commit['last_commit']:
            raise ExtensionIsUpToDateError('Extension %s is up-to-date' % ext_id)

        return gh_commit


def unzip(filename: str, ext_path: str) -> None:
    """
    1. Remove ext_path
    2. Extract zip into temp dir
    3. Move contents of <temp_dir>/<project_name>-master/* to ext_path
    """
    if os.path.exists(ext_path):
        rmtree(ext_path)

    temp_ext_path = mkdtemp(prefix='ulauncher_dl_')

    with ZipFile(filename) as zipfile:
        zipfile.extractall(temp_ext_path)

    for dir in os.listdir(temp_ext_path):
        move(os.path.join(temp_ext_path, dir), ext_path)
        # there is only one directory here, so return immediately
        return


def download_zip(url: str) -> str:
    dest_zip = mktemp('.zip', prefix='ulauncher_dl_')
    filename, _ = urlretrieve(url, dest_zip)

    return filename


class ExtensionDownloaderError(Exception):
    pass


class ExtensionNotFound(ExtensionDownloaderError):
    pass


class AlreadyDownloadedError(ExtensionDownloaderError):
    pass


class ExtensionIsUpToDateError(ExtensionDownloaderError):
    pass
