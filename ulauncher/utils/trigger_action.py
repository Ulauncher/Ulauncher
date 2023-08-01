import json

from gi.repository import Gio, GLib

from ulauncher.config import APP_ID, DBUS_PATH


def trigger_action(message: dict):
    json_message = json.dumps(message)
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    action_group = Gio.DBusActionGroup.get(bus, APP_ID, DBUS_PATH)
    action_group.activate_action("run-action", GLib.Variant.new_string(json_message))
