from __future__ import annotations

import logging
from shutil import rmtree

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb, ExtensionRecord
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.utils.get_icon_path import get_icon_path

logger = logging.getLogger()
ext_db = ExtensionDb.load()
ext_runner = ExtensionRunner.get_instance()


class ExtensionControllerError(Exception):
    pass


class ExtensionController:
    id: str

    def __init__(self, ext_id: str):
        self.id = ext_id
        if self.record.url:
            self.remote = ExtensionRemote(self.record.url)

    @classmethod
    def create_from_url(cls, url: str) -> ExtensionController:
        remote = ExtensionRemote(url)
        instance = cls(remote.extension_id)
        instance.remote = remote
        instance.record.url = url
        return instance

    @property
    def record(self) -> ExtensionRecord:
        return ext_db.get_record(self.id)

    @property
    def manifest(self) -> ExtensionManifest:
        return ExtensionManifest.load_from_extension_id(self.id)

    @property
    def path(self) -> str:
        ext_path = extension_finder.locate(self.id)
        assert ext_path, f"No extension could be found matching {self.id}"
        return ext_path

    @property
    def full_icon_path(self) -> str:
        return get_icon_path(self.manifest.icon, base_path=self.path)

    @property
    def is_manageable(self) -> bool:
        return extension_finder.is_manageable(self.path)

    @property
    def is_running(self) -> bool:
        return ext_runner.is_running(self.id)

    def download(self) -> None:
        self.remote.download()

    def remove(self) -> None:
        if not self.is_manageable:
            return

        self.stop()
        rmtree(self.path)
        # Update record to disabled if there is another version of the extension that can be found
        # Or remove the record otherwise
        if self.record:
            self.record.is_enabled = False
            if not extension_finder.locate(self.id):
                del ext_db[self.id]
            ext_db.save()

    def update(self) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        has_update, commit_hash = self.check_update()
        if not has_update:
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            self.id,
            self.record.commit_hash[:8],
            commit_hash[:8],
        )

        self.remote.download(commit_hash, warn_if_overwrite=False)
        return True

    def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = ExtensionRemote(self.record.url).get_compatible_hash()
        has_update = self.record.commit_hash != commit_hash
        return has_update, commit_hash

    def toggle_enabled(self, enabled: bool) -> None:
        self.record.is_enabled = enabled
        ext_db.save()
        if enabled:
            self.start()
        else:
            self.stop()

    def start(self):
        ext_runner.run(self.id)

    def stop(self):
        ext_runner.stop(self.id)
