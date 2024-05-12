from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from typing import Any, Generator
from weakref import WeakValueDictionary

from ulauncher.config import get_options, paths
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionIncompatibleRecoverableError,
    ExtensionManifest,
    ExtensionManifestError,
    UserPreference,
    UserTrigger,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime
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

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        if key == "last_commit":
            key = "commit_hash"
        if key == "last_commit_time":
            key = "commit_time"
        super().__setitem__(key, value)


logger = logging.getLogger()
verbose_logging: bool = get_options().verbose
controller_cache: WeakValueDictionary[str, ExtensionController] = WeakValueDictionary()
extension_runtimes: dict[str, ExtensionRuntime] = {}


class ExtensionControllerError(Exception):
    pass


class ExtensionController:
    id: str
    state: ExtensionState
    is_running: bool = False
    _path: str | None
    _state_path: Path

    def __init__(self, ext_id: str, path: str | None = None):
        self.id = ext_id
        self._path = path
        self._state_path = Path(f"{paths.EXTENSIONS_STATE}/{self.id}.json")
        self.state = ExtensionState.load(self._state_path)

        if not self.state.id:
            self.state.id = self.id
            defaults = json_load(f"{path}/.default-state.json")
            self.state.update(defaults)

        if self.state.url:
            self.remote = ExtensionRemote(self.state.url)

    @classmethod
    def create(cls, ext_id: str, path: str | None = None) -> ExtensionController:
        cached_controller = controller_cache.get(ext_id)
        if cached_controller:
            return cached_controller
        new_controller = cls(ext_id, path)
        controller_cache[ext_id] = new_controller
        return new_controller

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
            yield ExtensionController.create(ext_id, ext_path)

    @classmethod
    def get_from_keyword(cls, keyword: str) -> ExtensionController | None:
        for controller in controller_cache.values():
            for trigger in controller.user_triggers.values():
                if controller.is_running and keyword and keyword == trigger.user_keyword:
                    return controller

        return None

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
    def user_preferences(self) -> dict[str, UserPreference]:
        return self.manifest.get_user_preferences(self.id)

    @property
    def user_triggers(self) -> dict[str, UserTrigger]:
        return self.manifest.get_user_triggers(self.id)

    def save_user_preferences(self, data: Any) -> None:
        self.manifest.save_user_preferences(self.id, data)

    def get_normalized_icon_path(self, icon: str | None = None) -> str | None:
        return get_icon_path(icon or self.manifest.icon, base_path=self.path)

    async def download(self, commit_hash: str | None = None, warn_if_overwrite: bool = True) -> None:
        commit_hash, commit_timestamp = self.remote.download(commit_hash, warn_if_overwrite)
        self.state.update(
            commit_hash=commit_hash,
            commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
            updated_at=datetime.now().isoformat(),
            error_type="",
            error_message="",
        )
        self.state.save()

    async def remove(self) -> None:
        if not self.is_manageable:
            return

        await self.stop()
        rmtree(self.path)
        # Regenerate cached path in case extension still exists (installed elsewhere)
        self._path = extension_finder.locate(self.id)

        # If ^, then disable, else delete from db
        if self._path:
            self.state.is_enabled = False
            self.state.save()
        elif self._state_path.is_file():
            self._state_path.unlink()

    async def update(self) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        has_update, commit_hash = await self.check_update()
        was_running = self.is_running
        if not has_update:
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            self.id,
            self.state.commit_hash[:8],
            commit_hash[:8],
        )

        await self.stop()
        await self.download(commit_hash, warn_if_overwrite=False)
        return await self.toggle_enabled(was_running)

    async def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = ExtensionRemote(self.state.url).get_compatible_hash()
        has_update = self.state.commit_hash != commit_hash
        return has_update, commit_hash

    async def toggle_enabled(self, enabled: bool) -> bool:
        self.state.update(is_enabled=enabled, error_type="", error_message="")
        self.state.save()
        if enabled:
            return await self.start()
        await self.stop()
        return False

    def start_detached(self) -> None:
        if not self.is_running:

            def error_handler(error_type: str, error_msg: str) -> None:
                self.is_running = False
                extension_runtimes.pop(self.id, None)
                self.state.update(error_type=error_type, error_message=error_msg)
                self.state.save()

            try:
                self.manifest.validate()
                self.manifest.check_compatibility(verbose=True)
            except ExtensionManifestError as err:
                error_handler("Invalid", str(err))
                return
            except ExtensionIncompatibleRecoverableError as err:
                error_handler("Incompatible", str(err))
                return

            error_handler("", "")

            cmd = [sys.executable, f"{self.path}/main.py"]
            prefs = {id: pref.value for id, pref in self.user_preferences.items()}
            triggers = {id: t.keyword for id, t in self.manifest.triggers.items() if t.keyword}
            # backwards compatible v2 preferences format (with keywords added back)
            v2_prefs = {**triggers, **prefs}
            env = {
                "VERBOSE": str(int(verbose_logging)),
                "PYTHONPATH": paths.APPLICATION,
                "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            }

            extension_runtimes[self.id] = ExtensionRuntime(self.id, cmd, env, error_handler)

    async def start(self) -> bool:
        self.start_detached()
        for _ in range(100):
            if self.has_error:
                return False
            if self.is_running:
                return True
            await asyncio.sleep(0.1)
        return False

    async def stop(self) -> None:
        runtime = extension_runtimes.pop(self.id, None)
        if runtime:
            await runtime.stop()
            self.is_running = False

    @classmethod
    async def stop_all(cls) -> None:
        jobs = [c.stop() for c in controller_cache.values() if c.is_running]
        await asyncio.gather(*jobs)
