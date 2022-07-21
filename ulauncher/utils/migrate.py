import logging
import json
import os
import pickle
import sys
from pathlib import Path
from configparser import ConfigParser
from types import ModuleType
from ulauncher.utils.systemd_controller import UlauncherSystemdController

_logger = logging.getLogger()


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


def _migrate_file(from_path, to_path, transform=None):
    if not os.path.exists(to_path) and os.path.isfile(from_path):
        data = _load_legacy(Path(from_path))
        if data:
            _logger.info('Migrating %s to %s', from_path, to_path)
            if callable(transform):
                data = transform(data)
            _storeJSON(to_path, data)


def _migrate_app_state(old_format):
    new_format = {}
    for app_path, starts in old_format.items():
        # Was changed to use app ids instead of paths as keys
        new_format[os.path.basename(app_path)] = starts
    return new_format


def v5_to_v6(PATHS, is_first_run):
    # Convert extension prefs to JSON
    for file in Path(f"{PATHS.CONFIG}/ext_preferences").iterdir():
        if file.suffix in [".db", ".json"]:
            _migrate_file(str(file), f"{file.parent}/{file.stem}.json")

    # Convert app_stat.db to JSON and put in STATE_DIR
    _migrate_file(f"{PATHS.DATA}/app_stat_v2.db", f"{PATHS.STATE}/app_starts.json", _migrate_app_state)

    # Convert query_history.db to JSON and put in STATE_DIR
    # Needs a module hack for pickle because v5 stored these as the "ulauncher.search.Query" type
    MockQuery = ModuleType("Query")
    MockQuery.Query = str
    sys.modules["ulauncher.search.Query"] = MockQuery
    _migrate_file(f"{PATHS.DATA}/query_history.db", f"{PATHS.STATE}/query_history.json")
    del sys.modules["ulauncher.search.Query"]  # <-- Don't want this hack to remain in the runtime afterwards

    # Migrate autostart conf from XDG autostart file to systemd
    if is_first_run:
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


def v5_to_v6_destructive(PATHS):
    # Currently optional changes that breaks your conf if you want to revert back to v5 for some reason
    # We probably want to run these later as part of the v7 migration instead.

    # Delete old unused files
    cleanup_list = [
        *Path(PATHS.CONFIG).parent.rglob("autostart/ulauncher.desktop"),
        *Path(PATHS.CACHE).rglob("*.db"),
        *Path(PATHS.DATA).rglob("*.db"),
        *Path(PATHS.DATA).rglob("last.log"),
    ]
    if cleanup_list:
        print("Removing deprecated data files:")
        print("\n".join(map(str, cleanup_list)))
        for file in cleanup_list:
            file.unlink()

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
