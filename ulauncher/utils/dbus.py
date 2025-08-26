from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from gi.repository import Gio, GLib

from ulauncher import app_id, dbus_path

logger = logging.getLogger(__name__)


def is_app_running(app_id: str) -> bool:
    """Check if app is running by checking if the D-Bus service name is owned."""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    result = bus.call_sync(
        "org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "org.freedesktop.DBus",
        "NameHasOwner",
        GLib.Variant("(s)", (app_id,)),
        GLib.VariantType("(b)"),
        Gio.DBusCallFlags.NONE,
        -1,
    )
    unpacked = result.unpack()
    return bool(unpacked[0])


@lru_cache(maxsize=1)
def get_ulauncher_dbus_action_group() -> Gio.DBusActionGroup:
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    return Gio.DBusActionGroup.get(bus, app_id, dbus_path)


def dbus_trigger_event(name: str, message: Any | None = None) -> None:
    """Sends a D-Bus message to the Ulauncher App, which is delegated to the EventBus listener matching the name."""
    if not is_app_running(app_id):
        logger.debug("Ulauncher app is not running, skipping D-Bus trigger event: %s", name)
        return

    json_message = json.dumps({"name": name, "message": message})
    get_ulauncher_dbus_action_group().activate_action("trigger-event", GLib.Variant.new_string(json_message))
