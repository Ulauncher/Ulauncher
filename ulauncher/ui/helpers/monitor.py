from __future__ import annotations

import logging

from gi.repository import Gdk, GdkX11  # type: ignore[missing-module-attribute]

from ulauncher.gi import Gio

logger = logging.getLogger(__name__)


def _valid_geometry(display: Gdk.Display, geometry: Gdk.Rectangle) -> Gdk.Rectangle | None:
    # Compositors can report zero-sized monitors for disabled outputs, e.g. the primary on Hyprland
    if geometry.width > 0 and geometry.height > 0:
        return geometry
    logger.warning(
        "Invalid monitor geometry %sx%s at %s,%s (n_monitors=%s)",
        geometry.width,
        geometry.height,
        geometry.x,
        geometry.y,
        display.get_n_monitors(),
    )
    return None


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    display = Gdk.Display.get_default()
    if not display:
        logger.warning("Could not get default display")
        return None

    monitor: Gdk.Monitor | None = None
    if use_mouse_position:
        # GdkX11.X11Display.get_default() resolves to the inherited Gdk.Display.get_default(),
        # so on Wayland it returns the Wayland display, where the pointer position reads (0, 0)
        if (
            isinstance(display, GdkX11.X11Display)
            and (seat := display.get_default_seat())
            and (pointer := seat.get_pointer())
        ):
            (_, x, y) = pointer.get_position()
            monitor = display.get_monitor_at_point(x, y)
        else:
            logger.debug("Could not get mouse position (requires X11). Defaulting to primary or first monitor")

    monitor = monitor or display.get_primary_monitor() or display.get_monitor(0)
    if monitor and _valid_geometry(display, monitor.get_geometry()):
        return monitor
    return None


def get_monitor_geometries() -> list[Gdk.Rectangle]:
    display = Gdk.Display.get_default()
    if not display:
        logger.warning("Could not get default display")
        return []
    geometries = [
        monitor.get_geometry() for i in range(display.get_n_monitors()) if (monitor := display.get_monitor(i))
    ]
    return [geometry for geometry in geometries if _valid_geometry(display, geometry)]


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling

    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")
