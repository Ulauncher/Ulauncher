import logging
from gi.repository import Gdk, GdkX11, Gio  # type: ignore[attr-defined]
from ulauncher.utils.environment import IS_X11


logger = logging.getLogger()
if IS_X11:
    # pylint: disable=ungrouped-imports, no-name-in-module
    from gi.repository import Wnck  # type: ignore[attr-defined]

    wnck_screen = Wnck.Screen.get_default()


def get_monitor(use_mouse_position=False):
    """
    :rtype: class:Gdk.Monitor
    """
    display = Gdk.Display.get_default()

    if use_mouse_position:
        try:
            x11_display = GdkX11.X11Display.get_default()
            seat = x11_display.get_default_seat()
            (_, x, y) = seat.get_pointer().get_position()
            return display.get_monitor_at_point(x, y)
        # pylint: disable=broad-except
        except Exception as e:
            logger.exception("Unexpected exception: %s", e)

    return display.get_primary_monitor() or display.get_monitor(0)


def get_text_scaling_factor() -> int:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling
    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")  # type: ignore[arg-type]


def get_windows_stacked():
    wnck_screen.force_update()
    return reversed(wnck_screen.get_windows_stacked())


def get_xserver_time():
    return GdkX11.x11_get_server_time(Gdk.get_default_root_window())
