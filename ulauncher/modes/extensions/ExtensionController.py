from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from typing import Any, Generator

from ulauncher.config import PATHS, get_options
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.ExtensionManifest import (
    ExtensionIncompatibleWarning,
    ExtensionManifest,
    ExtensionManifestError,
    UserPreference,
    UserTrigger,
)
from ulauncher.modes.extensions.ExtensionRemote import ExtensionRemote
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.utils.get_icon_path import get_icon_path
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.json_utils import json_load


class ExtensionState(JsonConf):
    id = ""
    url = ""
    updated_at = ""
    commit_hash = ""
    commit_time = ""
    is_enabled = True
    error_message = ""
    error_type = ""

    def __setitem__(self, key, value):
        if key == "last_commit":
            key = "commit_hash"
        if key == "last_commit_time":
            key = "commit_time"
        super().__setitem__(key, value)


logger = logging.getLogger()
ext_runner = ExtensionRunner.get_instance()
verbose_logging: bool = get_options().verbose


class ExtensionControllerError(Exception):
    pass


class ExtensionController:
    id: str
    _path: str | None
    _state_path: Path

    def __init__(self, ext_id: str, path: str | None = None):
        self.id = ext_id
        self._path = path
        self._state_path = Path(f"{PATHS.EXTENSIONS_STATE}/{self.id}.json")

        if self.state.url:
            self.remote = ExtensionRemote(self.state.url)

    @classmethod
    def create_from_url(cls, url: str) -> ExtensionController:
        remote = ExtensionRemote(url)
        instance = cls(remote.ext_id)
        instance.remote = remote
        instance.state.url = url
        return instance

    @classmethod
    def iterate(cls) -> Generator[ExtensionController, None, None]:
        for ext_id, ext_path in extension_finder.iterate():
            yield ExtensionController(ext_id, ext_path)

    @property
    def state(self) -> ExtensionState:
        state = ExtensionState.load(self._state_path)
        # if id is missing it means no state exists, look for extension defaults
        if not state.id:
            defaults = json_load(f"{self.path}/.extension-record.json")
            state.update(defaults)
            state.id = self.id
        return state

    @property
    def manifest(self) -> ExtensionManifest:
        return ExtensionManifest.load(self.path)

    @property
    def path(self) -> str:
        if not self._path:
            self._path = extension_finder.locate(self.id)
        assert self._path, f"No extension could be found matching {self.id}"
        return self._path

    @property
    def is_enabled(self) -> bool:
        return self.state.is_enabled

    @property
    def has_error(self) -> bool:
        return bool(self.state.error_type)

    @property
    def is_manageable(self) -> bool:
        return extension_finder.is_manageable(self.path)

    @property
    def is_running(self) -> bool:
        return ext_runner.is_running(self.id)

    @property
    def user_preferences(self) -> dict[str, UserPreference]:
        return self.manifest.get_user_preferences(self.id)

    @property
    def user_triggers(self) -> dict[str, UserTrigger]:
        return self.manifest.get_user_triggers(self.id)

    def save_user_preferences(self, data: Any) -> None:
        self.manifest.save_user_preferences(self.id, data)

    def get_normalized_icon_path(self, icon: str | None = None) -> str:
        return get_icon_path(icon or self.manifest.icon, base_path=self.path)

    def download(self, commit_hash: str | None = None, warn_if_overwrite: bool = True) -> None:
        commit_hash, commit_timestamp = self.remote.download(commit_hash, warn_if_overwrite)
        self.state.update(
            commit_hash=commit_hash,
            commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self.state.save()

    def remove(self) -> None:
        if not self.is_manageable:
            return

        self.stop()
        rmtree(self.path)
        # Regenerate cached path in case extension still exists (installed elsewhere)
        self._path = extension_finder.locate(self.id)

        # If ^, then disable, else delete from db
        if self._path:
            self.state.is_enabled = False
            self.state.save()
        elif self._state_path.is_file():
            self._state_path.unlink()

    def update(self) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        has_update, commit_hash = self.check_update()
        was_running = self.is_running
        if not has_update:
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            self.id,
            self.state.commit_hash[:8],
            commit_hash[:8],
        )

        self.stop()
        self.download(commit_hash, warn_if_overwrite=False)

        if was_running:
            self.start()

        return True

    def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = ExtensionRemote(self.state.url).get_compatible_hash()
        has_update = self.state.commit_hash != commit_hash
        return has_update, commit_hash

    def toggle_enabled(self, enabled: bool) -> None:
        self.state.is_enabled = enabled
        self.state.save()
        if enabled:
            self.start()
        else:
            self.stop()

    def start(self):
        if not self.is_running:

            def error_handler(error_type: str, error_msg: str) -> None:
                self.state.update(error_type=error_type, error_message=error_msg)
                self.state.save()

            try:
                self.manifest.validate()
                self.manifest.check_compatibility(verbose=True)
            except ExtensionManifestError as err:
                error_handler("Invalid", str(err))
                return
            except ExtensionIncompatibleWarning as err:
                error_handler("Incompatible", str(err))
                return

            error_handler("", "")

            prefs = {id: pref.value for id, pref in self.user_preferences.items()}
            triggers = {id: t.keyword for id, t in self.manifest.triggers.items() if t.keyword}
            # backwards compatible v2 preferences format (with keywords added back)
            v2_prefs = {**triggers, **prefs}
            env = {
                "VERBOSE": str(int(verbose_logging)),
                "PYTHONPATH": PATHS.APPLICATION,
                "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            }

            ext_runner.run(self.id, self.path, env, error_handler)

    def stop(self):
        ext_runner.stop(self.id)
