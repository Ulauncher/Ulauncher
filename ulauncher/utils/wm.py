from __future__ import annotations

import logging

from gi.repository import Gdk, GdkX11, Gio  # type: ignore[attr-defined]

from ulauncher.utils.environment import IS_X11

logger = logging.getLogger()
if IS_X11:
    try:
        import gi

        gi.require_version("Wnck", "3.0")
        from gi.repository import Wnck  # type: ignore[attr-defined]
    except (ImportError, ValueError):
        Wnck = None
        logger.debug("Wnck is not installed")


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    """
    :rtype: class:Gdk.Monitor
    """
    display = Gdk.Display.get_default()
    assert display

    if use_mouse_position:
        try:
            x11_display = GdkX11.X11Display.get_default()
            seat = x11_display.get_default_seat()
            (_, x, y) = seat.get_pointer().get_position()
            return display.get_monitor_at_point(x, y)
        except Exception:
            logger.exception("Could not get monitor with X11. Defaulting to first or primary monitor")

    return display.get_primary_monitor() or display.get_monitor(0)


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling
    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")


def try_raise_app(app_id: str) -> bool:
    """
    Try to raise an app by id (str) and return whether successful
    Currently only supports X11 via Wnck
    """
    if IS_X11 and Wnck:
        wnck_screen = Wnck.Screen.get_default()
        wnck_screen.force_update()
        for win in reversed(wnck_screen.get_windows_stacked()):
            win_app_wm_id = (win.get_class_group_name() or "").lower()
            if win_app_wm_id == "thunar" and win.get_name().startswith("Bulk Rename"):
                # "Bulk Rename" identify as "Thunar": https://gitlab.xfce.org/xfce/thunar/-/issues/731
                win_app_wm_id = "thunar --bulk-rename"
            if win_app_wm_id == app_id:
                logger.info("Raising application %s", app_id)
                win.activate(GdkX11.x11_get_server_time(Gdk.get_default_root_window()))
                return True
    return False
