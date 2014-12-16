import logging
from gi.repository import Gdk, GdkX11

logger = logging.getLogger(__name__)


class Display(object):
    def __init__(self):
        self.screens = None

    def get_current_screen(self, window=None):
        try:
            if window:
                screen = self.default_screen.get_monitor_at_window(window.get_window())
            else:
                disp = GdkX11.X11Display.get_default()
                dm = Gdk.Display.get_device_manager(disp)
                pntr_device = dm.get_client_pointer()
                (src, x, y) = pntr_device.get_position()
                screen = self.default_screen.get_monitor_at_point(x, y)
        except:
            screen = 0
        return screen

    def get_current_screen_geometry(self, window=None):
        if not self.screens:
            self.get_screens()

        return self.screens[self.get_current_screen(window)]

    def get_screens(self):
        try:
            self.screens = []
            self.default_screen = Gdk.Screen.get_default()
            logger.debug("Found {0} monitor(s).".format(self.default_screen.get_n_monitors()))

            for i in range(self.default_screen.get_n_monitors()):
                rect = self.default_screen.get_monitor_geometry(i)
                logger.debug("  Monitor {0} - X: {1}, Y: {2}, W: {3}, H: {4}"
                             .format(i, rect.x, rect.y, rect.width, rect.height))
                self.screens.append({"x": rect.x,
                                     "y": rect.y,
                                     "width": rect.width,
                                     "height": rect.height})

        except Exception as e:
            logger.warning("Unable to find any video sources. Caught exception: %s" % e)

display = Display()
