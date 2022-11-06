import os
import logging
from urllib.request import urlretrieve
from tempfile import mktemp
from shutil import rmtree
from datetime import datetime
from typing import Tuple

from ulauncher.config import PATHS
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.untar import untar
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote


logger = logging.getLogger()


class ExtensionAlreadyInstalledWarning(Exception):
    pass


class ExtensionDownloaderError(Exception):
    pass


class ExtensionDownloader:

    @classmethod
    @singleton
    def get_instance(cls) -> 'ExtensionDownloader':
        ext_db = ExtensionDb.load()
        return cls(ext_db)

    def __init__(self, ext_db: ExtensionDb):
        super().__init__()
        self.ext_db = ext_db

    def download(self, url: str) -> str:
        """
        1. check if ext already exists
        2. get last commit info
        3. download & untar
        4. add it to the db

        :rtype: str
        :returns: Extension ID
        :raises AlreadyDownloadedError:
        """
        remote = ExtensionRemote(url)

        # 1. check if ext already exists
        ext_path = os.path.join(PATHS.EXTENSIONS, remote.extension_id)
        # allow user to re-download an extension if it's not running
        # most likely it has some problems with manifest file if it's not running
        if os.path.exists(ext_path):
            raise ExtensionAlreadyInstalledWarning(f'Extension with URL "{url}" is already installed')

        # 2. get last commit info
        commit_sha, commit_time = remote.get_latest_compatible_commit()

        # 3. download & untar
        filename = download_tarball(remote.get_download_url(commit_sha))
        untar(filename, ext_path, strip=1)

        # 4. add to the db
        self.ext_db.save({remote.extension_id: {
            'id': remote.extension_id,
            'url': url,
            'updated_at': datetime.now().isoformat(),
            'last_commit': commit_sha,
            'last_commit_time': commit_time
        }})

        return remote.extension_id

    def remove(self, ext_id: str) -> None:
        rmtree(os.path.join(PATHS.EXTENSIONS, ext_id))
        if ext_id in self.ext_db:
            del self.ext_db[ext_id]
            self.ext_db.save()

    def update(self, ext_id: str) -> bool:
        """
        :raises ExtensionDownloaderError:
        :rtype: boolean
        :returns: False if already up-to-date, True if was updated
        """
        has_update, commit_sha, commit_date = self.check_update(ext_id)
        if not has_update:
            return False
        ext = self._find_extension(ext_id)

        logger.info('Updating extension "%s" from commit %s to %s', ext_id,
                    ext.last_commit[:8], commit_sha[:8])

        remote = ExtensionRemote(ext.url)
        filename = download_tarball(remote.get_download_url(commit_sha))
        untar(filename, f"{PATHS.EXTENSIONS}/{ext_id}", strip=1)

        ext.update(
            updated_at=datetime.now().isoformat(),
            last_commit=commit_sha,
            last_commit_time=commit_date
        )

        self.ext_db.save({ext_id: ext})

        return True

    def check_update(self, ext_id: str) -> Tuple[bool, str, str]:
        """
        Returns tuple with commit info about a new version
        """
        ext = self._find_extension(ext_id)
        commit_sha, commit_time = ExtensionRemote(ext.url).get_latest_compatible_commit()
        can_update = ext.last_commit != commit_sha
        return can_update, commit_sha, commit_time

    def _find_extension(self, ext_id: str) -> ExtensionRecord:
        ext = self.ext_db.get(ext_id)
        if not ext:
            raise ExtensionDownloaderError("Extension not found")
        return ext


def download_tarball(url: str) -> str:
    dest_tar = mktemp('.tar.gz', prefix='ulauncher_dl_')
    filename, _ = urlretrieve(url, dest_tar)

    return filename
