from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from gi.repository import Gio, GLib

from ulauncher import app_id, dbus_path


@lru_cache(maxsize=1)
def get_dbus_action_group() -> Gio.DBusActionGroup:
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    return Gio.DBusActionGroup.get(bus, app_id, dbus_path)


def dbus_trigger_event(name: str, message: Any | None = None) -> None:
    """Sends a D-Bus message to the App, which is delegated to the EventBus listener matching the name."""
    json_message = json.dumps({"name": name, "message": message})
    get_dbus_action_group().activate_action("trigger-event", GLib.Variant.new_string(json_message))
