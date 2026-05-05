from __future__ import annotations

import logging

from ulauncher.gi import Gdk, GdkX11, Gio

logger = logging.getLogger()


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    display = Gdk.Display.get_default()
    if not display:
        logger.warning("Could not get default display")
        return None

    if use_mouse_position:
        if (
            (x11_display := GdkX11.X11Display.get_default())
            and (seat := x11_display.get_default_seat())
            and (pointer := seat.get_pointer())
        ):
            (_, x, y) = pointer.get_position()
            return display.get_monitor_at_point(x, y)
        logger.info("Could not get monitor with X11. Defaulting to first or primary monitor")

    return display.get_primary_monitor() or display.get_monitor(0)


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling

    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")
