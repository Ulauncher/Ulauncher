import os
import logging
from functools import lru_cache
from shutil import rmtree
from typing import Tuple

from ulauncher.config import PATHS
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote

logger = logging.getLogger()


class ExtensionDownloaderError(Exception):
    pass


class ExtensionDownloader:
    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls) -> "ExtensionDownloader":
        ext_db = ExtensionDb.load()
        return cls(ext_db)

    def __init__(self, ext_db: ExtensionDb):
        super().__init__()
        self.ext_db = ext_db

    def download(self, url: str) -> str:
        remote = ExtensionRemote(url)
        remote.download()
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
        has_update, commit_hash = self.check_update(ext_id)
        if not has_update:
            return False
        ext = self._find_extension(ext_id)

        logger.info('Updating extension "%s" from commit %s to %s', ext_id, ext.last_commit[:8], commit_hash[:8])

        remote = ExtensionRemote(ext.url)
        remote.download(commit_hash, overwrite=True)
        return True

    def check_update(self, ext_id: str) -> Tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        ext = self._find_extension(ext_id)
        commit_hash = ExtensionRemote(ext.url).get_compatible_hash()
        has_update = ext.last_commit != commit_hash
        return has_update, commit_hash

    def _find_extension(self, ext_id: str) -> ExtensionRecord:
        ext = self.ext_db.get(ext_id)
        if not ext:
            raise ExtensionDownloaderError("Extension not found")
        return ext
