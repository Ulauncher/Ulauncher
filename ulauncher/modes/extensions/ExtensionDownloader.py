from __future__ import annotations

import logging
from functools import lru_cache
from shutil import rmtree

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote

logger = logging.getLogger()


class ExtensionDownloaderError(Exception):
    pass


class ExtensionDownloader:
    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls) -> ExtensionDownloader:
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
        ext_path = extension_finder.locate(ext_id)
        assert ext_path, f"No extension could be found matching {ext_id}"
        if not extension_finder.is_manageable(ext_path):
            return

        rmtree(ext_path)
        # Update record to disabled if there is another version of the extension that can be found
        # Or remove the record otherwise
        record = self.ext_db.get(ext_id)
        if record:
            record.is_enabled = False
            try:
                extension_finder.locate(ext_id)
            except extension_finder.ExtensionNotFound:
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

        logger.info('Updating extension "%s" from commit %s to %s', ext_id, ext.commit_hash[:8], commit_hash[:8])

        remote = ExtensionRemote(ext.url)
        remote.download(commit_hash, warn_if_overwrite=False)
        return True

    def check_update(self, ext_id: str) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        ext = self._find_extension(ext_id)
        commit_hash = ExtensionRemote(ext.url).get_compatible_hash()
        has_update = ext.commit_hash != commit_hash
        return has_update, commit_hash

    def _find_extension(self, ext_id: str) -> ExtensionRecord:
        ext = self.ext_db.get(ext_id)
        if not ext:
            msg = "Extension not found"
            raise ExtensionDownloaderError(msg)
        return ext
