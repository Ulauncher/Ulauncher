from __future__ import annotations

import logging

from ulauncher.utils.environment import IS_X11

logger = logging.getLogger(__name__)


def try_raise_app(app_id: str) -> bool:
    """
    Try to raise an app by id (str) and return whether successful
    Currently only supports X11 via EWMH/Xlib
    """
    if IS_X11:
        try:
            from Xlib.display import Display

            from ulauncher.utils.x11_window_stack import activate_window, get_client_windows_top_first

            display = Display()
            for win in get_client_windows_top_first(display):
                wm_class = win.get_wm_class()
                if not wm_class:
                    logger.warning('Could not get the WM class for "%s". Will not be able to activate it.', app_id)
                    continue
                class_id, class_name = wm_class
                win_app_id = (class_id or "").lower()
                if win_app_id == "thunar" and (win.get_wm_name() or "").startswith("Bulk Rename"):
                    # "Bulk Rename" identify as "Thunar": https://gitlab.xfce.org/xfce/thunar/-/issues/731
                    # Also, note that get_wm_name is unreliable, but it works for Thunar https://github.com/parkouss/pyewmh/issues/15
                    win_app_id = "thunar --bulk-rename"
                if app_id == win_app_id or app_id == class_name.lower():
                    logger.info("Raising application %s", app_id)
                    activate_window(display, win)
                    return True

        except (ModuleNotFoundError, ImportError):
            logger.warning("python-xlib is required to use raise windows")

    return False
