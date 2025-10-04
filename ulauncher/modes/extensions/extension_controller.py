from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from ulauncher import paths
from ulauncher.cli import get_cli_args
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionIncompatibleRecoverableError,
    ExtensionManifest,
    ExtensionManifestError,
    ExtensionManifestPreference,
    ExtensionManifestTrigger,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime
from ulauncher.utils.get_icon_path import get_icon_path
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.json_utils import json_load


class ExtensionPreference(ExtensionManifestPreference):
    value: str | int | None = None


class ExtensionControllerTrigger(ExtensionManifestTrigger):
    pass


class ExtensionState(JsonConf):
    id = ""
    url = ""
    browser_url = ""
    updated_at = ""
    commit_hash = ""
    commit_time = ""
    is_enabled = True
    error_message = ""
    error_type = ""

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        if key == "last_commit":
            key = "commit_hash"
        elif key == "last_commit_time":
            key = "commit_time"
        super().__setitem__(key, value)


logger = logging.getLogger()
extension_runtimes: dict[str, ExtensionRuntime] = {}


def _load_preferences(ext_id: str) -> JsonConf:
    return JsonConf.load(f"{paths.EXTENSIONS_CONFIG}/{ext_id}.json")


class ExtensionController:
    id: str
    path: str
    state: ExtensionState
    manifest: ExtensionManifest
    is_manageable: bool
    is_running: bool = False
    _state_path: Path

    def __init__(self, ext_id: str, path: str) -> None:
        self.id = ext_id
        self.path = path
        self.manifest = ExtensionManifest.load(path)
        self.is_manageable = extension_finder.is_manageable(path)
        self._state_path = Path(f"{paths.EXTENSIONS_STATE}/{self.id}.json")
        self.state = ExtensionState.load(self._state_path)

        if not self.state.id:
            self.state.id = self.id
            defaults = json_load(f"{path}/.default-state.json")
            self.state.update(defaults)

    @property
    def is_enabled(self) -> bool:
        return self.state.is_enabled

    @property
    def has_error(self) -> bool:
        return bool(self.state.error_type)

    @property
    def preferences(self) -> dict[str, ExtensionPreference]:
        prefs_json = _load_preferences(self.id)
        prefs = {}
        for p_id, manifest_pref in self.manifest.preferences.items():
            # copy to avoid mutating
            pref = ExtensionPreference(**manifest_pref)
            pref.value = prefs_json.get("preferences", {}).get(p_id, manifest_pref.default_value)
            prefs[p_id] = pref
        return prefs

    @property
    def triggers(self) -> dict[str, ExtensionControllerTrigger]:
        user_prefs_json = _load_preferences(self.id)
        triggers = {}
        for t_id, manifest_trigger in self.manifest.triggers.items():
            trigger = ExtensionControllerTrigger(manifest_trigger)
            if user_keyword := user_prefs_json.get("triggers", {}).get(t_id, {}).get("keyword", trigger.keyword):
                trigger.keyword = user_keyword
            triggers[t_id] = trigger

        return triggers

    def save_user_preferences(self, data: Any) -> None:
        user_prefs_json = _load_preferences(self.id)
        user_prefs_json.save(data)

    def get_normalized_icon_path(self, icon: str | None = None) -> str | None:
        return get_icon_path(icon or self.manifest.icon, base_path=self.path)

    async def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = ExtensionRemote(self.state.url).get_compatible_hash()
        has_update = self.state.commit_hash != commit_hash
        return has_update, commit_hash

    async def toggle_enabled(self, enabled: bool) -> bool:
        self.state.save(is_enabled=enabled, error_type="", error_message="")
        if enabled:
            return await self.start()
        await self.stop()
        return False

    def start_detached(self) -> None:
        if not self.is_running:

            def exit_handler(error_type: str, error_msg: str) -> None:
                logger.error('Extension "%s" exited with an error: %s (%s)', self.id, error_msg, error_type)
                self.is_running = False
                extension_runtimes.pop(self.id, None)
                self.state.save(error_type=error_type, error_message=error_msg)

            try:
                self.manifest.validate()
                self.manifest.check_compatibility(verbose=True)
            except ExtensionManifestError as err:
                exit_handler("Invalid", str(err))
                return
            except ExtensionIncompatibleRecoverableError as err:
                exit_handler("Incompatible", str(err))
                return

            self.state.save(error_type="", error_message="")  # clear any previous error

            ext_deps = ExtensionDependencies(self.id, self.path)
            cmd = [sys.executable, f"{self.path}/main.py"]
            prefs = {p_id: pref.value for p_id, pref in self.preferences.items()}
            triggers = {t_id: t.keyword for t_id, t in self.manifest.triggers.items() if t.keyword}
            # backwards compatible v2 preferences format (with keywords added back)
            v2_prefs = {**triggers, **prefs}
            env = {
                "VERBOSE": str(int(get_cli_args().verbose)),
                "PYTHONPATH": ":".join(x for x in [paths.APPLICATION, ext_deps.get_dependencies_path()] if x),
                "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            }

            extension_runtimes[self.id] = ExtensionRuntime(self.id, cmd, env, exit_handler)

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
        if runtime := extension_runtimes.pop(self.id, None):
            await runtime.stop()
            self.is_running = False


class ExtensionNotFoundError(Exception):
    """Raised when an extension cannot be found by its ID or path."""
