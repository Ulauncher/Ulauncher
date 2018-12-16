import logging
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
            (src, x, y) = pntr_device.get_position()
            screen = default_screen.get_monitor_at_point(x, y)
    except Exception as e:
        logger.warning("Unexpected exception: %s" % e)
        screen = 0

    return screen


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
        logger.debug("Found {0} monitor(s).".format(default_screen.get_n_monitors()))

        for i in range(default_screen.get_n_monitors()):
            rect = default_screen.get_monitor_geometry(i)
            logger.debug("  Monitor {0} - X: {1}, Y: {2}, W: {3}, H: {4}"
                         .format(i, rect.x, rect.y, rect.width, rect.height))
            screens.append({"x": rect.x,
                            "y": rect.y,
                            "width": rect.width,
                            "height": rect.height})
    except Exception as e:
        raise RuntimeError("Unable to find any video sources: %s" % e)

    return screens
