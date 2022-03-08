import sys
import logging
from dbus import bus, service, SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from ulauncher.config import get_options

DBUS_SERVICE = 'net.launchpad.ulauncher'
DBUS_PATH = '/net/launchpad/ulauncher'
logger = logging.getLogger('ulauncher')
# Start DBus loop
DBusGMainLoop(set_as_default=True)

# If Ulauncher is already running, show the window of the running process, then exit the new process gracefully
if SessionBus().request_name(DBUS_SERVICE) != bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
    if get_options().no_window:
        logger.warning("Ulauncher is already running")
    else:
        SessionBus().get_object(DBUS_SERVICE, DBUS_PATH).get_dbus_method("toggle_window")()
    sys.exit(0)


class UlauncherDbusService(service.Object):
    def __init__(self, window):
        self.window = window
        bus_name = service.BusName(DBUS_SERVICE, bus=SessionBus())
        super().__init__(bus_name, DBUS_PATH)

    @service.method(DBUS_SERVICE)
    def toggle_window(self):
        self.window.toggle_window()
