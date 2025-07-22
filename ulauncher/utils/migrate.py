from __future__ import annotations

import json
import logging
import os
import pickle
import sys
from configparser import ConfigParser
from functools import partial
from pathlib import Path
from shutil import rmtree
from types import ModuleType
from typing import Any, Callable

from ulauncher import first_v6_run, paths
from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionState
from ulauncher.utils.json_utils import json_load
from ulauncher.utils.systemd_controller import SystemdController

_logger = logging.getLogger()
CACHE_PATH = os.path.join(os.environ.get("XDG_CACHE_HOME", f"{paths.HOME}/.cache"), "ulauncher_cache")  # See issue#40


def _load_legacy(path: Path) -> Any | None:
    try:
        if path.suffix == ".db":
            return pickle.loads(path.read_bytes())
        if path.suffix == ".json":
            return json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        _logger.warning('Could not migrate file "%s": %s', str(path), e)
    return None


def _store_json(path: str, data: Any) -> bool:
    try:
        Path(path).write_text(json.dumps(data, indent=4))
    except Exception as e:  # noqa: BLE001
        _logger.warning('Could not store JSON file "%s": %s', path, e)
        return False
    return True


def _migrate_file(
    from_path: str, to_path: str, transform: Callable[[Any], Any] | None = None, overwrite: bool = False
) -> None:
    if os.path.isfile(from_path) and (overwrite or not os.path.exists(to_path)):
        data = _load_legacy(Path(from_path))
        if data:
            _logger.info("Migrating %s to %s", from_path, to_path)
            if callable(transform):
                data = transform(data)
            _store_json(to_path, data)


def _migrate_app_state(old_format: dict[str, int]) -> dict[str, int]:
    new_format = {}
    for app_path, starts in old_format.items():
        # Was changed to use app ids instead of paths as keys
        new_format[os.path.basename(app_path)] = starts
    return new_format


def _migrate_user_prefs(ext_id: str, user_prefs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    # Check if already migrated
    if sorted(user_prefs.keys()) == ["preferences", "triggers"]:
        return user_prefs
    new_prefs: dict[str, dict[str, Any]] = {"preferences": {}, "triggers": {}}
    controller = ExtensionController.create(ext_id)
    for id, pref in user_prefs.items():
        try:
            if controller.manifest.triggers.get(id):
                new_prefs["triggers"][id] = {"keyword": pref}
            else:
                new_prefs["preferences"][id] = pref
        except AssertionError:
            _logger.warning("Could not convert preferences for extension (probably uninstalled): %s", ext_id)
    return new_prefs


def v5_to_v6() -> None:
    # Migrate extension state to individual files
    extension_db: dict[str, Any] = json_load(f"{paths.CONFIG}/extensions.json")
    for legacy_state in extension_db.values():
        ext_id = legacy_state["id"]
        state = ExtensionState.load(f"{paths.EXTENSIONS_STATE}/{ext_id}.json")
        if not state.id:  # don't overwrite if already migrated
            state.save(legacy_state)

    # Convert extension prefs to JSON
    ext_prefs = Path(paths.EXTENSIONS_CONFIG)
    # Migrate JSON to JSON first, assuming these are newer
    for file in ext_prefs.rglob("*.json"):
        _migrate_file(str(file), str(file), partial(_migrate_user_prefs, file.stem), overwrite=True)
    # Migrate db to JSON without overwrite. So if a JSON file exists it should never be overwritten
    # with data from a db file
    for file in ext_prefs.rglob("*.db"):
        _migrate_file(str(file), f"{file.parent}/{file.stem}.json", partial(_migrate_user_prefs, file.stem))

    # Convert app_stat.db to JSON and put in STATE_DIR
    _migrate_file(f"{paths.DATA}/app_stat_v2.db", f"{paths.STATE}/app_starts.json", _migrate_app_state)

    # Convert query_history.db to JSON and put in STATE_DIR
    # Needs a module hack for pickle because v5 stored these as the "ulauncher.search.Query" type
    mock_query = ModuleType("Query")
    mock_query.Query = str  # type: ignore[attr-defined]
    sys.modules["ulauncher.search.Query"] = mock_query
    _migrate_file(f"{paths.DATA}/query_history.db", f"{paths.STATE}/query_history.json")
    del sys.modules["ulauncher.search.Query"]  # <-- Don't want this hack to remain in the runtime afterwards

    # Convert show_recent_apps to max_recent_apps
    # Not using settings class because we don't want to convert the keys
    from ulauncher.utils.json_conf import JsonConf

    settings = JsonConf.load(f"{paths.CONFIG}/settings.json")
    legacy_recent_apps = settings.get("show_recent_apps") or settings.get("show-recent-apps")
    if legacy_recent_apps and settings.get("max_recent_apps") is None:
        # This used to be a boolean, but was converted to a numeric string in PR #576 in 2020
        # If people haven't changed their settings since 2020 it'll be set to 0
        settings.save(max_recent_apps=int(legacy_recent_apps) if str(legacy_recent_apps).isnumeric() else 0)

    # Migrate autostart conf from XDG autostart file to systemd
    if first_v6_run:
        try:
            systemd_unit = SystemdController("ulauncher")
            autostart_file = Path(f"{paths.CONFIG}/../autostart/ulauncher.desktop").resolve()
            if os.path.exists(autostart_file) and systemd_unit.can_start():
                autostart_config = ConfigParser()
                autostart_config.read(autostart_file)
                if autostart_config["Desktop Entry"]["X-GNOME-Autostart-enabled"] == "true":
                    if systemd_unit.can_start():
                        systemd_unit.toggle(True)
                    elif systemd_unit.supported:
                        _logger.warning("Can't enable systemd unit. Not installed")
                    else:
                        _logger.warning("Can't enable systemd unit. Systemd does not have systemd")
            _logger.info("Applied autostart settings to systemd")
        except Exception as e:  # noqa: BLE001
            _logger.warning("Couldn't migrate autostart: %s", e)


def v5_to_v6_destructive() -> None:
    # Currently optional changes that breaks your conf if you want to revert back to v5 for some reason
    # We probably want to run these later as part of the v7 migration instead.

    # Delete old unused files
    cleanup_list = [
        *Path(paths.CONFIG).parent.rglob("autostart/ulauncher.desktop"),
        *Path(CACHE_PATH).rglob("*.db"),
        *Path(paths.DATA).rglob("*.db"),
        *Path(paths.DATA).rglob("last.log"),
        Path(f"{paths.CONFIG}/extensions.json"),
    ]
    if cleanup_list:
        print("Removing deprecated data files:")  # noqa: T201
        print("\n".join(map(str, cleanup_list)))  # noqa: T201
        for file in cleanup_list:
            file.unlink()

    if Path(CACHE_PATH).is_dir():
        print(f"Removing deprecated cache directory '{CACHE_PATH}'")  # noqa: T201
        rmtree(CACHE_PATH)

    # Delete old preferences
    from ulauncher.utils.json_conf import JsonConf

    settings = JsonConf.load(f"{paths.CONFIG}/settings.json")
    _logger.info("Pruning settings")
    settings.save({"blacklisted_desktop_dirs": None, "show_recent_apps": None, "show-recent-apps": None})
