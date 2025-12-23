from __future__ import annotations

from typing import Any, Callable

from gi.repository import Gio, GLib


def _get_interface_settings() -> Gio.Settings | None:
    try:
        return Gio.Settings.new("org.gnome.desktop.interface")
    except GLib.Error:
        return None


def system_prefers_dark(interface_settings: Gio.Settings | None = None) -> bool:
    """Return True when the desktop prefers a dark theme."""
    interface_settings = interface_settings or _get_interface_settings()
    if interface_settings is None:
        return False

    keys = set(interface_settings.list_keys())
    if "color-scheme" in keys and interface_settings.is_writable("color-scheme"):
        value = interface_settings.get_string("color-scheme")
        if value == "prefer-dark":
            return True
        if value in {"prefer-light", "default"}:
            return False

    return False


class SystemThemeWatcher:
    """Watch GNOME interface settings and emit dark preference updates."""

    def __init__(self, on_change: Callable[[bool], None]) -> None:
        self._on_change = on_change
        self.interface_settings = _get_interface_settings()
        self._handler_ids: list[int] = []

        if self.interface_settings is None:
            return

        if "color-scheme" in self.interface_settings.list_keys():
            handler_id = self.interface_settings.connect("changed::color-scheme", self._on_settings_changed)
            self._handler_ids.append(handler_id)

    def start(self) -> None:
        if self.interface_settings is None:
            return
        self._emit()

    def disconnect(self) -> None:
        if self.interface_settings is None:
            return
        for handler_id in self._handler_ids:
            self.interface_settings.disconnect(handler_id)
        self._handler_ids.clear()

    def _on_settings_changed(self, *_args: Any) -> None:
        self._emit()

    def _emit(self) -> None:
        self._on_change(system_prefers_dark(self.interface_settings))
