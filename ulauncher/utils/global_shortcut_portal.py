"""
Client for the XDG Desktop Portal GlobalShortcuts interface.

Registers Ulauncher's "show window" shortcut with the desktop environment via
org.freedesktop.portal.GlobalShortcuts, so the DE owns the binding, shows its own
configuration UI, and activates us on key press - the same model as the per-DE
integrations this replaces, but working on any DE/compositor with a portal backend
(GNOME 48+, Plasma, Hyprland, COSMIC, ...).

We run unsandboxed, so we must identify ourselves with
org.freedesktop.host.portal.Registry.Register (mandatory with xdg-desktop-portal
1.21+). app_id is reverse-DNS and backed by an installed .desktop file, which
GNOME's backend additionally requires.

The portal API is asynchronous (handles arrive via org.freedesktop.portal.Request
Response signals), so everything is callback-based on the GLib main loop.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from ulauncher import app_id
from ulauncher.gi import Gio, GLib

logger = logging.getLogger(__name__)

PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
GLOBAL_SHORTCUTS_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
REQUEST_INTERFACE = "org.freedesktop.portal.Request"
REGISTRY_INTERFACE = "org.freedesktop.host.portal.Registry"

SHORTCUT_ID = "show-ulauncher"
SHORTCUT_DESCRIPTION = "Show Ulauncher"
# Preferred trigger in XDG shortcuts spec syntax (modifiers separated by "+").
# Backends may ignore it and let the user pick keys in the consent dialog.
SHORTCUT_TRIGGER = "CTRL+space"


class GlobalShortcutsPortal:
    """One GlobalShortcuts portal session, binding Ulauncher's shortcut."""

    session_handle: str | None = None
    # DE-provided human text of the currently assigned keys, e.g. "Press <Control>space"
    trigger_description: str | None = None
    # time.monotonic() of the last Activated signal for our shortcut
    activated_at: float | None = None
    on_activate: Callable[[], None]
    _portal: Gio.DBusProxy

    def __init__(self, on_activate: Callable[[], None]) -> None:
        self.on_activate = on_activate

    def bind(self) -> None:
        """Start binding the shortcut. Results and errors are logged, not raised."""
        self._register_host_app()
        Gio.DBusProxy.new_for_bus(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            PORTAL_BUS_NAME,
            PORTAL_OBJECT_PATH,
            GLOBAL_SHORTCUTS_INTERFACE,
            None,
            self._on_proxy_created,
        )

    def _register_host_app(self) -> None:
        """Declare our app id to the portal registry (xdg-desktop-portal 1.20+).

        Without this, 1.21+ rejects CreateSession from unsandboxed apps whose systemd
        scope doesn't derive a valid app id. Pre-1.20 portals don't have the
        interface, so failure here is not fatal.
        """
        try:
            Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                PORTAL_BUS_NAME,
                PORTAL_OBJECT_PATH,
                REGISTRY_INTERFACE,
                None,
            ).call_sync("Register", GLib.Variant("(sa{sv})", (app_id, {})), Gio.DBusCallFlags.NONE, 2000)
            logger.debug("Registered app id '%s' with the portal registry", app_id)
        except GLib.Error as e:
            logger.debug("Portal registry Register failed (older portals don't have it): %s", e)

    def _on_proxy_created(self, _source: Gio.DBusProxy, result: Gio.AsyncResult) -> None:
        try:
            self._portal = Gio.DBusProxy.new_for_bus_finish(result)
            self._create_session()
        except GLib.Error:
            logger.warning("GlobalShortcuts portal not available")

    def _create_session(self) -> None:
        token = _handle_token()
        _await_response(_request_path(token), self._on_session_created)
        self._portal.call(
            "CreateSession",
            GLib.Variant(
                "(a{sv})",
                (
                    {
                        "handle_token": GLib.Variant("s", token),
                        "session_handle_token": GLib.Variant("s", "ulauncher"),
                    },
                ),
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            self._on_session_request_created,
            None,
        )

    def _on_session_request_created(self, _proxy: Gio.DBusProxy, result: Gio.AsyncResult, _user_data: None) -> None:
        try:
            self._portal.call_finish(result).unpack()
        except GLib.Error as e:
            logger.warning("Failed to create GlobalShortcuts portal session: %s", e)

    def _on_session_created(self, results: GLib.Variant) -> None:
        # The docs claim the session handle is an object path, but backends shipped it as a string
        self.session_handle = results.unpack()["session_handle"]
        logger.debug("GlobalShortcuts portal session created: %s", self.session_handle)
        token = _handle_token()
        _await_response(_request_path(token), self._on_bound)
        self._portal.call(
            "BindShortcuts",
            GLib.Variant(
                "(oa(sa{sv})sa{sv})",
                (
                    self.session_handle,
                    [
                        (
                            SHORTCUT_ID,
                            {
                                "description": GLib.Variant("s", SHORTCUT_DESCRIPTION),
                                "preferred_trigger": GLib.Variant("s", SHORTCUT_TRIGGER),
                            },
                        )
                    ],
                    "",
                    {"handle_token": GLib.Variant("s", token)},
                ),
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            self._on_bind_request_created,
            None,
        )

    def _on_bind_request_created(self, _proxy: Gio.DBusProxy, result: Gio.AsyncResult, _user_data: None) -> None:
        try:
            self._portal.call_finish(result).unpack()
        except GLib.Error as e:
            logger.warning("Failed to call BindShortcuts: %s", e)

    def _on_bound(self, results: GLib.Variant) -> None:
        bound = results.unpack()["shortcuts"]
        if not bound:
            logger.warning("Global shortcut binding was rejected or cancelled")
            return
        for shortcut_id, props in bound:
            if shortcut_id == SHORTCUT_ID and "trigger_description" in props:
                self.trigger_description = props["trigger_description"]
        logger.debug("Global shortcut bound: %s", SHORTCUT_TRIGGER)
        self._portal.connect("g-signal", self._on_g_signal)

    def _on_g_signal(
        self, _proxy: Gio.DBusProxy, _sender: str | None, signal_name: str, parameters: GLib.Variant
    ) -> None:
        if signal_name == "Activated":
            session_handle, shortcut_id, _timestamp, _options = parameters.unpack()
            if session_handle == self.session_handle and shortcut_id == SHORTCUT_ID:
                self.activated_at = time.monotonic()
                self.on_activate()
        elif signal_name == "ShortcutsChanged":
            for shortcut_id, props in parameters.unpack()[1]:
                if shortcut_id == SHORTCUT_ID and "trigger_description" in props:
                    self.trigger_description = props["trigger_description"]

    def configure(self) -> bool:
        """Ask the portal to show its shortcut configuration UI (portal interface version 2)."""
        if not self.session_handle:
            logger.warning("Cannot configure shortcuts: no portal session")
            return False
        try:
            self._portal.call_sync(
                "ConfigureShortcuts",
                GLib.Variant("(osa{sv})", (self.session_handle, "", {})),
                Gio.DBusCallFlags.NONE,
                5000,
            )
        except GLib.Error as e:
            logger.warning("ConfigureShortcuts failed: %s", e)
            return False
        return True


def _handle_token() -> str:
    """Token appended to request/session handle paths; must be a valid path element."""
    return f"ulauncher_{uuid.uuid4().hex[:8]}"


def is_available() -> bool:
    """Whether a portal service exposing GlobalShortcuts is on the session bus.

    Checks the interface version property: the bus name is owned by
    xdg-desktop-portal even on desktops where no GlobalShortcuts backend exists.
    """
    try:
        proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_AUTO_START,
            None,
            PORTAL_BUS_NAME,
            PORTAL_OBJECT_PATH,
            GLOBAL_SHORTCUTS_INTERFACE,
            None,
        )
    except GLib.Error:
        return False
    return bool(proxy.get_cached_property("version"))


def _request_path(token: str) -> str:
    """Predicted path of the Request object for a call with this handle_token.

    The portal derives the handle from our unique bus name and the token, so we can
    subscribe to the Response signal before making the call (signals sent between
    the call and a late subscription would otherwise be lost).
    """
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    sender = bus.get_unique_name()
    if not sender:
        logger.warning("No unique bus name; portal requests can't be tracked")
        return ""
    return f"/org/freedesktop/portal/desktop/request/{sender[1:].replace('.', '_')}/{token}"


def _await_response(request_path: str, on_response: Callable[[GLib.Variant], None]) -> None:
    """Wait for a portal request's Response signal and pass its results to on_response.

    A request only responds once, so the subscription is removed on the first signal.
    """
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    subscription_id: list[int] = []

    def on_signal(
        _connection: Gio.DBusConnection,
        _sender: str | None,
        _path: str | None,
        _interface: str | None,
        _signal: str | None,
        parameters: GLib.Variant,
    ) -> None:
        if subscription_id:
            bus.signal_unsubscribe(subscription_id.pop())
        # Response is (response_code u, results a{sv}); keep the results as a Variant
        # so callbacks can unpack them themselves
        response_code = parameters.get_child_value(0).get_uint32()
        if response_code == 0:
            on_response(parameters.get_child_value(1))
        else:
            logger.warning("GlobalShortcuts portal request failed with code %s", response_code)

    subscription_id.append(
        bus.signal_subscribe(
            sender=PORTAL_BUS_NAME,
            interface_name=REQUEST_INTERFACE,
            member="Response",
            object_path=request_path,
            arg0=None,
            flags=Gio.DBusSignalFlags.NONE,
            callback=on_signal,
        )
    )
