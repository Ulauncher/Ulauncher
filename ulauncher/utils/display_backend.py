"""Map the display_backend setting to a GDK_BACKEND override."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ulauncher.utils.environment import DESKTOP_ID, IS_X11
from ulauncher.utils.lru_cache import lru_cache

if TYPE_CHECKING:
    from ulauncher.utils.settings import DisplayBackend

GNOME_XWAYLAND_MIN_VERSION = 50


# Synchronous D-Bus call which blocks the main thread for up to its timeout
@lru_cache(maxsize=None)
def gnome_shell_major_version() -> int | None:
    from ulauncher.gi import Gio, GLib

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        reply = bus.call_sync(
            "org.gnome.Shell",
            "/org/gnome/Shell",
            "org.freedesktop.DBus.Properties",
            "Get",
            GLib.Variant("(ss)", ("org.gnome.Shell", "ShellVersion")),
            None,
            Gio.DBusCallFlags.NONE,
            1000,
            None,
        )
        version = reply.get_child_value(0).unpack()
        return int(version.split(".")[0])
    except (GLib.Error, ValueError):
        return None


def xwayland_preferable_for_de() -> bool:
    """Resolve true when the app behaves better in XWayland than pure Wayland."""
    if IS_X11 or DESKTOP_ID != "GNOME":
        return False
    # Pantheon reports GNOME; the lookup below fails there and yields False.
    version = gnome_shell_major_version()
    return version is not None and version >= GNOME_XWAYLAND_MIN_VERSION


def resolve(display_backend: DisplayBackend) -> Literal["x11"] | None:
    """GDK_BACKEND a setting forces on its own, or None for the session default."""
    if display_backend == "x11" or (display_backend == "auto" and xwayland_preferable_for_de()):
        return "x11"
    return None


def preferred_backend(display_backend: DisplayBackend, external_backend: str | None) -> str | None:
    """GDK_BACKEND Ulauncher should run with.

    A user-exported GDK_BACKEND overrides auto and system, but an explicit x11
    setting overrides the environment.
    """
    # settings.json holds no runtime type validation, so an unexpected value may persist there
    if display_backend not in ("auto", "system", "x11"):
        display_backend = "auto"
    if display_backend == "x11":
        return "x11"
    return external_backend or resolve(display_backend)
