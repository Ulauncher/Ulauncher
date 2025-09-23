from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, TypeVar, cast

from gi.repository import Gio, GLib

from ulauncher import app_id, dbus_path

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    return Gio.DBusActionGroup.get(bus, app_id, dbus_path)


def dbus_trigger_event(name: str, message: Any | None = None, wait: bool = False) -> T | None:
    """Sends a D-Bus message to the Ulauncher App, which is delegated to the EventBus listener matching the name.

    Args:
        name: Event name to trigger
        message: Optional message data to send with the event
        wait: If True, wait for the event handler to complete before returning

    Returns:
        The result of the D-Bus call if wait=True, None otherwise
    """
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)

    if not check_app_running(app_id, bus):
        logger.debug("Ulauncher app is not running, skipping D-Bus trigger event: %s", name)
        return None

    json_message = json.dumps({"name": name, "message": message})
    action_group = get_ulauncher_dbus_action_group(bus)

    if wait:
        result = bus.call_sync(
            bus_name=app_id,
            object_path=dbus_path,
            interface_name="org.gtk.Actions",
            method_name="Activate",
            parameters=GLib.Variant("(sava{sv})", ("trigger-event", [GLib.Variant.new_string(json_message)], {})),
            reply_type=None,
            flags=Gio.DBusCallFlags.NONE,
            timeout_msec=-1,
            cancellable=None,
        )
        return cast("T", result)

    # Use asynchronous call (original behavior)
    action_group.activate_action("trigger-event", GLib.Variant.new_string(json_message))
    return None
