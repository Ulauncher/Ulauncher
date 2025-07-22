from __future__ import annotations

from typing import Any

from ulauncher import paths
from ulauncher.utils.json_conf import JsonConf

_settings_file = f"{paths.CONFIG}/settings.json"


class Settings(JsonConf):
    disable_desktop_filters = False
    clear_previous_query = True
    close_on_focus_out = True
    grab_mouse_pointer = False
    hotkey_show_app = ""  # Note that this is no longer used, other than for migrating to the DE wrapper
    jump_keys = "1234567890abcdefghijklmnopqrstuvwxyz"
    enable_application_mode = True
    max_recent_apps = 0
    base_width = 750
    raise_if_started = False
    render_on_screen = "mouse-pointer-monitor"
    show_tray_icon = True
    terminal_command = ""
    theme_name = "light"
    arrow_key_aliases = "hjkl"
    daemonless = False
    tray_icon_name = "ulauncher-indicator-symbolic"

    # Convert dash to underscore
    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        if key.replace("-", "_") == "show_indicator_icon":
            key = "show_tray_icon"
        super().__setitem__(key.replace("-", "_"), value)

    def get_jump_keys(self) -> list[str]:
        # convert to list and filter out duplicates
        return list(dict.fromkeys(list(self.jump_keys)))

    @classmethod
    def load(cls) -> Settings:  # type: ignore[override]
        return super().load(_settings_file)
