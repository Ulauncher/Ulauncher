from __future__ import annotations

import contextlib
from typing import Any, Literal

from ulauncher import paths
from ulauncher.data import Err, JsonConf
from ulauncher.utils.json_utils import json_load_dict, json_save
from ulauncher.utils.lru_cache import lru_cache

_settings_file = f"{paths.CONFIG}/settings.json"
DisplayBackend = Literal["auto", "system", "x11"]


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


class Settings(JsonConf):
    arrow_key_aliases: str = "hjkl"
    auto_resume: bool = False
    base_width: int = 750
    close_on_focus_out: bool = True
    disable_desktop_filters: bool = False
    display_backend: DisplayBackend = "auto"
    enable_application_mode: bool = True
    grab_mouse_pointer: bool = False
    hotkey_show_app: str = ""  # No longer used, other than to trigger the global shortcut setup on first run
    jump_keys: str = "1234567890abcdefghijklmnopqrstuvwxyz"
    keep_alive: bool = True
    layer_shell: bool = True
    max_recent_apps: int = 0
    raise_if_started: bool = False
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
