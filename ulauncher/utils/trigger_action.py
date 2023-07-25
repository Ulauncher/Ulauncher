import json

from gi.repository import Gio, GLib

from ulauncher.config import APP_ID, DBUS_PATH
from ulauncher.utils.decorator.run_async import run_async


@run_async
def trigger_action(message: dict):
    json_message = json.dumps(message)
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    proxy = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None, APP_ID, DBUS_PATH, f"{APP_ID}.actions")
    args_variants = GLib.Variant.new_tuple(GLib.Variant.new_string(json_message))
    proxy.call("RunAction", args_variants, Gio.DBusCallFlags.NO_AUTO_START, 500)
