from __future__ import annotations

import contextlib
import logging
from typing import Any, Literal

from ulauncher import paths
from ulauncher.data import Err, JsonConf
from ulauncher.utils.json_utils import json_load_dict, json_save
from ulauncher.utils.lru_cache import lru_cache

logger = logging.getLogger(__name__)
_settings_file = f"{paths.CONFIG}/settings.json"
DisplayBackend = Literal["auto", "system", "x11"]
RecentAppsLayout = Literal["list", "grid"]
RecentAppsGridLabels = Literal["none", "name", "shortcut", "name-and-shortcut"]

# settings.json is meant to be hand-editable, so a numeric setting can arrive as a string like
# "4", or outside the range its spin button allows. Gtk.Adjustment rejects a string outright and
# the layout arithmetic raises on it. Out of range is worse than cosmetic: the grid pads its last
# row with one filler widget per unused column, so "100000" columns would hang the window, and an
# unbounded icon size is loaded at that size. Normalizing on write covers loading the file,
# saving from the UI and hand edits in one place.
# Bounds mirror the spin buttons in ulauncher/ui/preferences/views/preferences.py.
_INT_SETTINGS: dict[str, tuple[int, int]] = {
    "base_width": (540, 2000),
    "max_recent_apps": (0, 20),
    "recent_apps_grid_columns": (1, 12),
    "recent_apps_grid_icon_size": (16, 128),
    "window_shadow": (0, 25),
}

# Same reasoning for the settings typed as a Literal. An unknown value reaches the widgets, which
# match it against the values they know and quietly fall through: an unrecognized label mode would
# render tiles with no labels at all, while the preferences combo shows the default, so the UI and
# the window disagree about what is configured.
_ENUM_SETTINGS: dict[str, tuple[str, ...]] = {
    "recent_apps_grid_labels": ("none", "name", "shortcut", "name-and-shortcut"),
    "recent_apps_layout": ("list", "grid"),
}


# TODO: Remove this some time after v6 stable (give people some month to migrate)
@lru_cache(maxsize=None)  # cached so it only runs once per session
def _drop_legacy_recent_apps(path: str) -> None:
    """
    Drop show_recent_apps to prevent it from overriding max_recent_apps. Needed because
    The old migration left the legacy show_recent_apps in the file.
    """
    with contextlib.suppress(OSError):
        data = json_load_dict(path)
        if "max_recent_apps" in data and ("show_recent_apps" in data or "show-recent-apps" in data):
            data.pop("show_recent_apps", None)
            data.pop("show-recent-apps", None)
            json_save(data, path, sort_keys=True)


def _as_bounded_int(key: str, value: Any) -> int:
    """Coerce a numeric setting to an int within its bounds, or fall back to its default."""
    lower, upper = _INT_SETTINGS[key]
    try:
        return min(upper, max(lower, int(value)))
    # json.loads reads Infinity and 1e400 as a float infinity, which int() rejects with
    # OverflowError rather than ValueError. Letting that escape would break Settings.load().
    except (OverflowError, TypeError, ValueError):
        default = getattr(Settings, key)
        logger.warning('Invalid value %r for setting "%s", using %s instead', value, key, default)
        return int(default)


def _as_known_enum(key: str, value: Any) -> str:
    """Keep an enum setting to the values the code handles, or fall back to its default."""
    if value in _ENUM_SETTINGS[key]:
        return value
    default = getattr(Settings, key)
    logger.warning('Invalid value %r for setting "%s", using "%s" instead', value, key, default)
    return str(default)


class Settings(JsonConf):
    arrow_key_aliases: str = "hjkl"
    auto_resume: bool = False
    base_width: int = 750
    close_on_focus_out: bool = True
    disable_desktop_filters: bool = False
    display_backend: DisplayBackend = "auto"
    enable_application_mode: bool = True
    grab_mouse_pointer: bool = False
    hotkey_show_app: str = ""  # Note that this is no longer used, other than for migrating to the DE wrapper
    jump_keys: str = "1234567890abcdefghijklmnopqrstuvwxyz"
    keep_alive: bool = True
    layer_shell: bool = True
    max_recent_apps: int = 0
    raise_if_started: bool = False
    recent_apps_grid_columns: int = 4
    recent_apps_grid_icon_size: int = 48
    recent_apps_grid_labels: RecentAppsGridLabels = "name-and-shortcut"
    recent_apps_layout: RecentAppsLayout = "list"
    render_on_screen: str = "mouse-pointer-monitor"
    show_tray_icon: bool = True
    terminal_command: str = ""
    theme_name: str = "light"
    tray_icon_name: str = "ulauncher-indicator-symbolic"
    window_shadow: int = 5

    # Convert dash to underscore
    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        normalized = key.replace("-", "_")
        if normalized == "show_indicator_icon":
            normalized = "show_tray_icon"
        elif normalized == "daemonless":
            normalized = "keep_alive"
            value = not value
        elif normalized == "clear_previous_query":
            normalized = "auto_resume"
            value = not value
        elif normalized == "show_recent_apps":
            # This used to be a boolean, but was converted to a numeric string in PR #576 in 2020
            # If people haven't changed their settings since 2020 it'll be set to 0
            value = int(value) if str(value).isnumeric() else 0
            normalized = "max_recent_apps"
        if normalized in _INT_SETTINGS:
            value = _as_bounded_int(normalized, value)
        elif normalized in _ENUM_SETTINGS:
            value = _as_known_enum(normalized, value)
        super().__setitem__(normalized, value)

    def get_jump_keys(self) -> list[str]:
        # convert to list and filter out duplicates
        return list(dict.fromkeys(list(self.jump_keys)))

    def is_persistent(self) -> bool:
        """Whether the app should be kept alive after the window is closed.

        Uses systemd when available, falling back to keep_alive.
        """
        from ulauncher.utils.systemd_controller import SystemdController

        result = SystemdController("ulauncher").status()
        if isinstance(result, Err):
            return self.keep_alive
        status = result.value
        if status.can_start:
            return status.is_enabled
        return self.keep_alive

    @classmethod
    def load(cls, *, force: bool = False) -> Settings:  # type: ignore[override]
        _drop_legacy_recent_apps(_settings_file)

        return super().load(_settings_file, force=force)
