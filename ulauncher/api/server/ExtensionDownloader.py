import os
import logging
from zipfile import ZipFile
from urllib.request import urlretrieve
from tempfile import mktemp, mkdtemp
from shutil import rmtree, move
from datetime import datetime
from ulauncher.utils.mypy_extensions import TypedDict

from ulauncher.config import EXTENSIONS_DIR
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.api.shared.errors import UlauncherAPIError, ErrorName
from ulauncher.api.server.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.api.server.GithubExtension import GithubExtension
from ulauncher.api.server.ExtensionRunner import ExtensionRunner, ExtensionIsNotRunningError
from ulauncher.api.server.extension_finder import find_extensions


logger = logging.getLogger(__name__)


class ExtensionDownloaderError(UlauncherAPIError):
    pass


class ExtensionIsUpToDateError(Exception):
    pass


LastCommit = TypedDict('LastCommit', {
    'last_commit': str,
    'last_commit_time': str
})


class ExtensionDownloader:

    @classmethod
    @singleton
    def get_instance(cls) -> 'ExtensionDownloader':
        ext_db = ExtensionDb.get_instance()
        ext_runner = ExtensionRunner.get_instance()
        return cls(ext_db, ext_runner)

    def __init__(self, ext_db: ExtensionDb, ext_runner: ExtensionRunner):
        super().__init__()
        self.ext_db = ext_db
        self.ext_runner = ext_runner

    def download(self, url: str) -> str:
        """
        1. check if ext already exists
        2. get last commit info
        3. download & unzip
        4. add it to the db

        :rtype: str
        :returns: Extension ID
        :raises AlreadyDownloadedError:
        """
        gh_ext = GithubExtension(url)
        gh_ext.validate_url()

        # 1. check if ext already exists
        ext_id = gh_ext.get_ext_id()
        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)
        # allow user to re-download an extension if it's not running
        # most likely it has some problems with manifest file if it's not running
        if os.path.exists(ext_path) and self.ext_runner.is_running(ext_id):
            raise ExtensionDownloaderError('Extension with URL "%s" is already added' % url,
                                           ErrorName.ExtensionAlreadyAdded)

        # 2. get last commit info
        commit = gh_ext.find_compatible_version()

        # 3. download & unzip
        filename = download_zip(gh_ext.get_download_url(commit['sha']))
        unzip(filename, ext_path)

        # 4. add to the db
        self.ext_db.put(ext_id, {
            'id': ext_id,
            'url': url,
            'updated_at': datetime.now().isoformat(),
            'last_commit': commit['sha'],
            'last_commit_time': commit['time'].isoformat()
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
        :raises ExtensionDownloaderError:
        :rtype: boolean
        :returns: False if already up-to-date, True if was updated
        """
        commit = self.get_new_version(ext_id)
        ext = self._find_extension(ext_id)

        logger.info('Updating extension "%s" from commit %s to %s', ext_id,
                    ext['last_commit'][:8], commit['last_commit'][:8])

        if self.ext_runner.is_running(ext_id):
            self.ext_runner.stop(ext_id)

        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)

        gh_ext = GithubExtension(ext['url'])
        filename = download_zip(gh_ext.get_download_url(commit['last_commit']))
        unzip(filename, ext_path)

        ext['updated_at'] = datetime.now().isoformat()
        ext['last_commit'] = commit['last_commit']
        ext['last_commit_time'] = commit['last_commit_time']
        self.ext_db.put(ext_id, ext)
        self.ext_db.commit()

        self.ext_runner.run(ext_id)

        return True

    def get_new_version(self, ext_id: str) -> LastCommit:
        """
        Returns dict with commit info about a new version or raises ExtensionIsUpToDateError
        """
        ext = self._find_extension(ext_id)
        url = ext['url']
        gh_ext = GithubExtension(url)
        commit = gh_ext.find_compatible_version()
        need_update = ext['last_commit'] != commit['sha']
        if not need_update:
            raise ExtensionIsUpToDateError('Extension is up to date')

        return {
            'last_commit': commit['sha'],
            'last_commit_time': commit['time'].isoformat()
        }

    def _find_extension(self, ext_id: str) -> ExtensionRecord:
        ext = self.ext_db.find(ext_id)
        if not ext:
            raise ExtensionDownloaderError("Extension not found", ErrorName.UnexpectedError)
        return ext


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
