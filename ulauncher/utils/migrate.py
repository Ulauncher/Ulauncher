import logging
import json
import os
import pickle
import sys
from shutil import rmtree
from functools import partial
from pathlib import Path
from configparser import ConfigParser
from types import ModuleType
from ulauncher.config import PATHS, FIRST_V6_RUN
from ulauncher.utils.systemd_controller import UlauncherSystemdController
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest

_logger = logging.getLogger()
CACHE_PATH = os.path.join(os.environ.get("XDG_CACHE_HOME", f"{PATHS.HOME}/.cache"), "ulauncher_cache")  # See issue#40


def _load_legacy(path: Path):
    try:
        if path.suffix == ".db":
            return pickle.loads(path.read_bytes())
        if path.suffix == ".json":
            return json.loads(path.read_text())
    except Exception as e:
        _logger.warning('Could not migrate file "%s": %s', str(path), e)
    return None


def _storeJSON(path, data):
    try:
        Path(path).write_text(json.dumps(data, indent=4))
        return True
    except Exception as e:
        _logger.warning('Could not store JSON file "%s": %s', path, e)
        return False


def _migrate_file(from_path, to_path, transform=None, overwrite=False):
    if os.path.isfile(from_path) and (overwrite or not os.path.exists(to_path)):
        data = _load_legacy(Path(from_path))
        if data:
            _logger.info("Migrating %s to %s", from_path, to_path)
            if callable(transform):
                data = transform(data)
            _storeJSON(to_path, data)


def _migrate_app_state(old_format):
    new_format = {}
    for app_path, starts in old_format.items():
        # Was changed to use app ids instead of paths as keys
        new_format[os.path.basename(app_path)] = starts
    return new_format


def _migrate_user_prefs(extension_id, user_prefs):
    # Check if alreay migrated
    if sorted(user_prefs.keys()) == ["preferences", "triggers"]:
        return user_prefs
    new_prefs = {"preferences": {}, "triggers": {}}
    manifest = ExtensionManifest.new_from_file(f"{PATHS.EXTENSIONS}/{extension_id}/manifest.json")
    for id, pref in user_prefs.items():
        if manifest.triggers.get(id):
            new_prefs["triggers"][id] = {"keyword": pref}
        else:
            new_prefs["preferences"][id] = pref
    return new_prefs


def v5_to_v6():
    # Convert extension prefs to JSON
    EXT_PREFS = Path(PATHS.EXTENSIONS_CONFIG)
    # Migrate JSON to JSON first, assuming these are newer
    for file in EXT_PREFS.rglob("*.json"):
        _migrate_file(str(file), str(file), partial(_migrate_user_prefs, file.stem), overwrite=True)
    # Migrate db to JSON without overwrite. So if a JSON file exists it should never be overwritten
    # with data from a db file
    for file in EXT_PREFS.rglob("*.db"):
        _migrate_file(str(file), f"{file.parent}/{file.stem}.json", partial(_migrate_user_prefs, file.stem))

    # Convert app_stat.db to JSON and put in STATE_DIR
    _migrate_file(f"{PATHS.DATA}/app_stat_v2.db", f"{PATHS.STATE}/app_starts.json", _migrate_app_state)

    # Convert query_history.db to JSON and put in STATE_DIR
    # Needs a module hack for pickle because v5 stored these as the "ulauncher.search.Query" type
    MockQuery = ModuleType("Query")
    MockQuery.Query = str
    sys.modules["ulauncher.search.Query"] = MockQuery
    _migrate_file(f"{PATHS.DATA}/query_history.db", f"{PATHS.STATE}/query_history.json")
    del sys.modules["ulauncher.search.Query"]  # <-- Don't want this hack to remain in the runtime afterwards

    # Convert show_recent_apps to max_recent_apps
    # Not using settings class because we don't want to convert the keys
    # pylint: disable=import-outside-toplevel
    from ulauncher.utils.json_data import JsonData

    settings = JsonData.new_from_file(f"{PATHS.CONFIG}/settings.json")
    legacy_recent_apps = settings.get("show_recent_apps") or settings.get("show-recent-apps")
    if legacy_recent_apps and settings.get("max_recent_apps") is None:
        # This used to be a boolean, but was converted to a numeric string in PR #576 in 2020
        # If people haven't changed their settings since 2020 it'll be set to 0
        settings.save(max_recent_apps=int(legacy_recent_apps) if str(legacy_recent_apps).isnumeric() else 0)

    # Migrate autostart conf from XDG autostart file to systemd
    if FIRST_V6_RUN:
        try:
            systemd_unit = UlauncherSystemdController()
            AUTOSTART_FILE = Path(f"{PATHS.CONFIG}/../autostart/ulauncher.desktop").resolve()
            if os.path.exists(AUTOSTART_FILE) and systemd_unit.is_allowed():
                autostart_config = ConfigParser()
                autostart_config.read(AUTOSTART_FILE)
                if autostart_config["Desktop Entry"]["X-GNOME-Autostart-enabled"] == "true":
                    systemd_unit.switch(True)
            _logger.info("Applied autostart settings to systemd")
        except Exception as e:
            _logger.warning("Couldn't migrate autostart: %s", e)


def v5_to_v6_destructive():
    # Currently optional changes that breaks your conf if you want to revert back to v5 for some reason
    # We probably want to run these later as part of the v7 migration instead.

    # Delete old unused files
    cleanup_list = [
        *Path(PATHS.CONFIG).parent.rglob("autostart/ulauncher.desktop"),
        *Path(CACHE_PATH).rglob("*.db"),
        *Path(PATHS.DATA).rglob("*.db"),
        *Path(PATHS.DATA).rglob("last.log"),
    ]
    if cleanup_list:
        print("Removing deprecated data files:")
        print("\n".join(map(str, cleanup_list)))
        for file in cleanup_list:
            file.unlink()

    if Path(CACHE_PATH).is_dir():
        print(f"Removing deprecated cache directory '{CACHE_PATH}'")
        rmtree(CACHE_PATH)

    # Delete old preferences
    # pylint: disable=import-outside-toplevel
    from ulauncher.utils.json_data import JsonData

    settings = JsonData.new_from_file(f"{PATHS.CONFIG}/settings.json")
    _logger.info("Pruning settings")
    settings.save({"blacklisted_desktop_dirs": None, "show_recent_apps": None, "show-recent-apps": None})

    # Update icon locations for shortcuts.json generated before v6
    # (v6 created symlinks for them for backwards compatibility, but when v6 comes we should delete the symlinks)
    shortcuts_conf = Path(f"{PATHS.CONFIG}/shortcuts.json")
    shortcuts_text = shortcuts_conf.read_text()
    shortcuts_replace = {
        "/media/google-search-icon.png": "/icons/google-search.png",
        "/media/stackoverflow-icon.svg": "/icons/stackoverflow.svg",
        "/media/wikipedia-icon.png": "/icons/wikipedia.png",
    }

    for old_path, new_path in shortcuts_replace.items():
        if old_path in shortcuts_text:
            _logger.info('Updating shortcut icon from "%s" to "%s"', old_path, new_path)
            shortcuts_text.replace(old_path, new_path)

    shortcuts_conf.write_text(shortcuts_text)
