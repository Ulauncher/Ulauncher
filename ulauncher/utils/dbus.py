from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from gi.repository import Gio, GLib

import ulauncher

logger = logging.getLogger(__name__)


def dbus_query_freedesktop(
    bus: Gio.DBusConnection,
    method_name: str,
    parameters: GLib.Variant | None = None,
    response_type: GLib.VariantType | None = None,
    flags: Gio.DBusCallFlags | None = None,
    timeout_msec: int | None = None,
    cancellable: Gio.Cancellable | None = None,
) -> GLib.Variant:
    """Helper function to query the standard D-Bus interface org.freedesktop.DBus."""
    return bus.call_sync(
        bus_name="org.freedesktop.DBus",
        object_path="/org/freedesktop/DBus",
        interface_name="org.freedesktop.DBus",
        method_name=method_name,
        parameters=parameters,
        reply_type=response_type,
        flags=flags or Gio.DBusCallFlags.NONE,
        timeout_msec=timeout_msec or -1,
        cancellable=cancellable,
    )


def check_app_running(app_id: str, bus: Gio.DBusConnection | None = None) -> bool:
    """Check if app is running by checking if the D-Bus service name is owned."""
    params = GLib.Variant("(s)", (app_id,))
    response_type = GLib.VariantType("(b)")
    bus = bus or Gio.bus_get_sync(Gio.BusType.SESSION)
    (is_running,) = dbus_query_freedesktop(bus, "NameHasOwner", params, response_type).unpack()
    return bool(is_running)


def get_app_pid(app_id: str) -> int | None:
    """Get the PID of a D-Bus app"""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)

    if not check_app_running(app_id, bus):
        return None

    get_owner_params = GLib.Variant("(s)", (app_id,))
    get_owner_response_type = GLib.VariantType("(s)")
    (owner,) = dbus_query_freedesktop(bus, "GetNameOwner", get_owner_params, get_owner_response_type).unpack()

    get_pid_params = GLib.Variant("(s)", (owner,))
    get_pid_response_type = GLib.VariantType("(u)")
    (pid,) = dbus_query_freedesktop(bus, "GetConnectionUnixProcessID", get_pid_params, get_pid_response_type).unpack()
    return int(pid)


@lru_cache(maxsize=1)
def get_ulauncher_dbus_action_group(bus: Gio.DBusConnection) -> Gio.DBusActionGroup:
    return Gio.DBusActionGroup.get(bus, ulauncher.app_id, ulauncher.dbus_path)


def dbus_trigger_event(name: str, *args: Any) -> None:
    """Sends a D-Bus message to the Ulauncher App, which is delegated to the EventBus listener matching the name."""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)

    if not check_app_running(ulauncher.app_id, bus):
        logger.debug("Ulauncher app is not running, skipping D-Bus trigger event: %s", name)
        return

    json_message = json.dumps({"name": name, "args": list(args)})
    get_ulauncher_dbus_action_group(bus).activate_action("trigger-event", GLib.Variant.new_string(json_message))
