from __future__ import annotations

from typing import Any

from ulauncher import paths
from ulauncher.data import JsonConf

_settings_file = f"{paths.CONFIG}/settings.json"


class Settings(JsonConf):
    arrow_key_aliases: str = "hjkl"
    auto_resume: bool = False
    base_width: int = 750
    close_on_focus_out: bool = True
    disable_desktop_filters: bool = False
    enable_application_mode: bool = True
    grab_mouse_pointer: bool = False
    hotkey_show_app: str = ""  # Note that this is no longer used, other than for migrating to the DE wrapper
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
        super().__setitem__(normalized, value)

    def get_jump_keys(self) -> list[str]:
        # convert to list and filter out duplicates
        return list(dict.fromkeys(list(self.jump_keys)))

    def is_persistent(self) -> bool:
        """Whether the app should be kept alive after the window is closed.

        Uses systemd when available, falling back to keep_alive.
        """
        from ulauncher.utils.systemd_controller import SystemdController

        status = SystemdController("ulauncher").status()
        if status.can_start:
            return status.is_enabled
        return self.keep_alive

    @classmethod
    def load(cls, *, force: bool = False) -> Settings:  # type: ignore[override]
        return super().load(_settings_file, force=force)
