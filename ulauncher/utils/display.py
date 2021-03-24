import logging
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkX11', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gdk, GdkX11

logger = logging.getLogger(__name__)


def get_current_screen(window=None):
    """
    :rtype int:
    """
    default_screen = Gdk.Screen.get_default()
    try:
        if window:
            screen = default_screen.get_monitor_at_window(window.get_window())
        else:
            disp = GdkX11.X11Display.get_default()
            dm = Gdk.Display.get_device_manager(disp)
            pntr_device = dm.get_client_pointer()
            (_, x, y) = pntr_device.get_position()
            screen = default_screen.get_monitor_at_point(x, y)
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception("Unexpected exception: %s", e)
        screen = 0

    return screen


def get_primary_screen_geometry():
    """
    :returns: dict with keys: x, y, width, height
    """
    return get_screens()[Gdk.Screen.get_default().get_primary_monitor()]


def get_monitor_scale_factor() -> int:
    # TODO: use scaling factor of a monitor where ulauncher window is going to be displayed
    try:
        return Gdk.Display.get_default().get_primary_monitors().get_scale_factor()
    except AttributeError:  # Fallback to support GTK <3.22
        screen = Gdk.Screen.get_default()
        prim_monitor_num = screen.get_primary_monitor()
        return screen.get_monitor_scale_factor(prim_monitor_num)


def get_current_screen_geometry(window=None):
    """
    :returns: dict with keys: x, y, width, height
    """
    return get_screens()[get_current_screen(window)]


def get_screens():
    """
    :returns: a list of screen geometries
    :raises RuntimeError:
    """

    screens = []
    try:
        default_screen = Gdk.Screen.get_default()
        logger.debug("Found %s monitor(s)", default_screen.get_n_monitors())

        for i in range(default_screen.get_n_monitors()):
            rect = default_screen.get_monitor_geometry(i)
            logger.debug("  Monitor %s - X: %s, Y: %s, W: %s, H: %s", i, rect.x, rect.y, rect.width, rect.height)
            screens.append({"x": rect.x,
                            "y": rect.y,
                            "width": rect.width,
                            "height": rect.height})
    except Exception as e:
        raise RuntimeError("Unable to find any video sources: %s" % e)

    return screens
