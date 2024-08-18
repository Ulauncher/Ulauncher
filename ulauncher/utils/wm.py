from __future__ import annotations

import logging

from gi.repository import Gdk, GdkX11, Gio  # type: ignore[attr-defined]

from ulauncher.utils.environment import IS_X11

logger = logging.getLogger()


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
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
    Currently only supports X11 via EWMH/Xlib
    """
    if IS_X11:
        try:
            from ulauncher.utils.ewmh import EWMH

            ewmh = EWMH()
            for win in reversed(ewmh.getClientListStacking()):
                wm_class = win.get_wm_class()
                if not wm_class:
                    logger.warning('Could not get the WM class for "%s". Will not be able to activate it.', app_id)
                    return False
                class_id, class_name = wm_class
                win_app_id = (class_id or "").lower()
                if win_app_id == "thunar" and win.get_wm_name().startswith("Bulk Rename"):
                    # "Bulk Rename" identify as "Thunar": https://gitlab.xfce.org/xfce/thunar/-/issues/731
                    # Also, note that get_wm_name is unreliable, but it works for Thunar https://github.com/parkouss/pyewmh/issues/15
                    win_app_id = "thunar --bulk-rename"
                if app_id == win_app_id or app_id == class_name.lower():
                    logger.info("Raising application %s", app_id)
                    ewmh.setActiveWindow(win)
                    ewmh.display.flush()
                    return True

        except ModuleNotFoundError:
            pass

    return False
