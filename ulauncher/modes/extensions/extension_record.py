from __future__ import annotations

import logging
from datetime import datetime
from os.path import isfile, join
from pathlib import Path
from shutil import rmtree
from typing import Any

from ulauncher import paths
from ulauncher.data import BaseDataClass, JsonConf
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionManifest,
    ExtensionManifestPreference,
)
from ulauncher.utils.json_utils import json_load


class ExtensionPreference(ExtensionManifestPreference):
    value: str | int | bool | None = None


class ExtensionRecordTrigger(BaseDataClass):
    name = ""
    description = ""
    default_keyword = ""
    icon = ""
    keyword = ""


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


logger = logging.getLogger(__name__)


def _load_preferences(ext_id: str) -> JsonConf:
    return JsonConf.load(f"{paths.EXTENSIONS_CONFIG}/{ext_id}.json")


class ExtensionRecord:
    """Represents an installed extension: its files, state and preferences."""

    id: str
    path: str
    state: ExtensionState
    _state_path: Path

    is_preview = False

    def __init__(self, ext_id: str, path: str) -> None:
        self.id = ext_id
        self.path = path
        _state_path = f"{paths.EXTENSIONS_STATE}/{self.id}.json"
        self._state_path = Path(_state_path)
        self.state = ExtensionState.load(_state_path)
        self._seed_default_state()

    def _seed_default_state(self) -> None:
        """Seed a brand-new extension's state from its bundled .default-state.json. No-op once seeded,
        or while the files are absent, so an install that downloads them later seeds afterward."""
        if self.state.id or not Path(self.path).exists():
            return
        self.state.id = self.id
        defaults = json_load(f"{self.path}/.default-state.json")
        if isinstance(defaults, dict):
            self.state.update(defaults)

    @property
    def manifest(self) -> ExtensionManifest:
        return ExtensionManifest.load(self.path)

    @property
    def is_enabled(self) -> bool:
        return self.is_preview or (self.state.is_enabled and not self.has_error)

    @property
    def has_error(self) -> bool:
        # A preview must not surface the installed extension's persisted error; it reports as a preview.
        return not self.is_preview and bool(self.state.error_type)

    @property
    def is_manageable(self) -> bool:
        return extension_finder.is_manageable(self.path)

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
    def triggers(self) -> dict[str, ExtensionRecordTrigger]:
        user_prefs_json = _load_preferences(self.id)
        triggers = {}
        for t_id, manifest_trigger in self.manifest.triggers.items():
            trigger = ExtensionRecordTrigger(manifest_trigger)
            trigger.keyword = user_prefs_json.get("triggers", {}).get(t_id, {}).get("keyword", trigger.default_keyword)
            triggers[t_id] = trigger

        return triggers

    def persist_preferences(self, data: Any) -> None:
        """Write the preferences to disk."""
        user_prefs_json = _load_preferences(self.id)
        user_prefs_json.save(data)

    def get_icon_value(self, icon: str | None = None) -> str:
        icon_value = icon or self.manifest.icon
        expanded_path = join(self.path, icon_value)
        if isfile(expanded_path):
            return expanded_path
        return icon_value

    def remove(self) -> bool:
        """Delete the extension's files and state. Returns whether the files were removed.

        Use ExtensionRegistry.uninstall instead of calling this directly; it also stops a running
        process first and handles a non-manageable copy taking over the removed extension's id.
        """
        if not self.is_manageable:
            logger.warning(
                "Extension %s is not manageable. Cannot remove it automatically. "
                "Please remove it manually from the extensions directory: %s",
                self.id,
                self.path,
            )
            return False

        rmtree(self.path)
        logger.info("Extension %s uninstalled successfully", self.id)

        if self._state_path.is_file():
            self._state_path.unlink()
        return True

    def save_installed_state(self, commit_hash: str, commit_timestamp: float, **extra_state: Any) -> None:
        """Refresh the manifest cache and state after an install or update swapped in new files."""
        ExtensionManifest.load(self.path, force=True)  # bust the path cache so the swapped-in files win
        self._seed_default_state()
        self.state.save(
            **extra_state,
            commit_hash=commit_hash,
            commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
            updated_at=datetime.now().isoformat(),
            error_type="",
            error_message="",
        )


class PreviewExtensionRecord(ExtensionRecord):
    """An extension being previewed from a dev path via the CLI; `path` is the dev path.

    Only one runs at a time (the debugger binds a fixed port). While active, it replaces the
    installed extension with the same id in the registry, so that id launches from the dev path.
    """

    is_preview = True
    with_debugger = False

    def __init__(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        super().__init__(ext_id, path)
        self.with_debugger = with_debugger

    @property
    def is_manageable(self) -> bool:
        """Never manageable, so remove/update cannot delete or replace the dev checkout."""
        return False
