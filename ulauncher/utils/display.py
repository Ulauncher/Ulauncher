import logging
import gi
gi.require_versions({
    'Gio': '2.0',
    'Gdk': '3.0',
    'GdkX11': '3.0',
})
# pylint: disable=wrong-import-position
from gi.repository import Gdk, GdkX11, Gio

logger = logging.getLogger(__name__)


def get_monitor_geometry(use_mouse_position=True):
    """
    :rtype int:
    """
    default_screen = Gdk.Screen.get_default()
    monitor_nr = default_screen.get_primary_monitor()
    if use_mouse_position:
        try:
            (_, x, y) = GdkX11.X11Display.get_default().get_default_seat().get_pointer().get_position()
            monitor_nr = default_screen.get_monitor_at_point(x, y)
        # pylint: disable=broad-except
        except Exception as e:
            logger.exception("Unexpected exception: %s", e)

    return default_screen.get_monitor_geometry(monitor_nr)


def get_scaling_factor() -> int:
    # These two are rougly the same thing as the latter doesn't apply only to text
    # Text_scaling allow fractional scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    monitor_scaling = Gdk.Display.get_default().get_primary_monitor().get_scale_factor()
    text_scaling = Gio.Settings.new("org.gnome.desktop.interface").get_double('text-scaling-factor')
    return monitor_scaling * text_scaling
