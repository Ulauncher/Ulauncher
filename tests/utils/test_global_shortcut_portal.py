from __future__ import annotations

from typing import Callable
from typing import cast as typing_cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.gi import GLib
from ulauncher.utils import global_shortcut_portal
from ulauncher.utils.global_shortcut_portal import (
    GLOBAL_SHORTCUTS_INTERFACE,
    PORTAL_OBJECT_PATH,
    SHORTCUT_DESCRIPTION,
    SHORTCUT_ID,
    SHORTCUT_TRIGGER,
    GlobalShortcutsPortal,
)

SESSION_HANDLE = "/org/freedesktop/portal/desktop/session/1_23/ulauncher_token"
SENDER = ":1.23"


class FakeBus:
    """Records signal subscriptions so tests can deliver portal signals manually."""

    def __init__(self) -> None:
        self.unique_name = SENDER
        self.subs: dict[str, Callable[..., None]] = {}
        self.unsubscribed: list[int] = []

    def get_unique_name(self) -> str:
        return self.unique_name

    def signal_subscribe(self, **kwargs: object) -> int:
        assert kwargs["sender"] == "org.freedesktop.portal.Desktop"
        assert kwargs["interface_name"] == "org.freedesktop.portal.Request"
        assert kwargs["member"] == "Response"
        assert kwargs["arg0"] is None  # no arg0 filtering: the match is on the object path
        callback = typing_cast("Callable[..., None]", kwargs["callback"])
        object_path = typing_cast("str", kwargs["object_path"])
        self.subs[object_path] = callback
        return len(self.subs)

    def signal_unsubscribe(self, subscription_id: int) -> None:
        self.unsubscribed.append(subscription_id)

    def deliver_response(self, token: str, code: int, results: dict[str, GLib.Variant]) -> None:
        path = f"/org/freedesktop/portal/desktop/request/{SENDER[1:].replace('.', '_')}/{token}"
        callback = self.subs.pop(path)
        callback(None, SENDER, path, None, "Response", GLib.Variant("(ua{sv})", (code, results)))


@pytest.fixture
def gio(mocker: MockerFixture) -> MagicMock:
    """The Gio module inside the portal client, with a FakeBus behind bus_get_sync."""
    gio = mocker.patch("ulauncher.utils.global_shortcut_portal.Gio")
    bus = FakeBus()
    gio.bus_get_sync.return_value = bus
    gio.portal_bus = bus
    return gio


@pytest.fixture
def portal_proxy(gio: MagicMock, mocker: MockerFixture) -> MagicMock:
    """Mock DBusProxy created by bind(), after simulating the async creation."""
    gio.DBusProxy.new_for_bus_sync.return_value = MagicMock(name="registry_proxy")
    proxy = MagicMock(name="portal_proxy")
    gio.DBusProxy.new_for_bus_finish.return_value = proxy

    def finish_proxy_creation() -> MagicMock:
        callback = gio.DBusProxy.new_for_bus.call_args[0][7]
        callback(None, mocker.Mock())
        return proxy

    gio.finish_proxy_creation = finish_proxy_creation
    return proxy


def test_is_available__false_when_portal_missing(gio: MagicMock) -> None:
    gio.DBusProxy.new_for_bus_sync.side_effect = GLib.Error("no such name")

    assert global_shortcut_portal.is_available() is False


def test_is_available__true_when_version_advertised(gio: MagicMock) -> None:
    proxy = gio.DBusProxy.new_for_bus_sync.return_value
    proxy.get_cached_property.return_value = GLib.Variant("u", 2)

    assert global_shortcut_portal.is_available() is True
    proxy.get_cached_property.assert_called_once_with("version")


def test_is_available__false_without_version_property(gio: MagicMock) -> None:
    proxy = gio.DBusProxy.new_for_bus_sync.return_value
    proxy.get_cached_property.return_value = None

    assert global_shortcut_portal.is_available() is False


def test_bind__registers_app_id_before_creating_proxy(gio: MagicMock, mocker: MockerFixture) -> None:
    registry_proxy = gio.DBusProxy.new_for_bus_sync.return_value

    GlobalShortcutsPortal(lambda: None).bind()

    registry_proxy.call_sync.assert_called_once_with(
        "Register",
        mocker.ANY,
        gio.DBusCallFlags.NONE,
        2000,  # type: ignore[attr-defined]
    )
    args = gio.DBusProxy.new_for_bus.call_args[0]
    assert args[3:6] == ("org.freedesktop.portal.Desktop", PORTAL_OBJECT_PATH, GLOBAL_SHORTCUTS_INTERFACE)


def test_bind__flow(gio: MagicMock, portal_proxy: MagicMock) -> None:
    """CreateSession -> BindShortcuts -> Activated, driven through the Response signals."""
    activated: list[bool] = []
    portal = GlobalShortcutsPortal(lambda: activated.append(True))

    portal.bind()
    gio.finish_proxy_creation()

    # CreateSession requested with a token, and its Response awaited up front
    session_call = portal_proxy.call.call_args_list[0]
    assert session_call[0][0] == "CreateSession"
    options = session_call[0][1].unpack()[0]
    session_token = options["handle_token"]
    gio.portal_bus.deliver_response(session_token, 0, {"session_handle": GLib.Variant("o", SESSION_HANDLE)})
    assert portal.session_handle == SESSION_HANDLE

    # BindShortcuts requested with our shortcut
    bind_call = portal_proxy.call.call_args_list[1]
    assert bind_call[0][0] == "BindShortcuts"
    session_handle, shortcuts, parent_window, bind_options = bind_call[0][1].unpack()
    assert session_handle == SESSION_HANDLE
    assert parent_window == ""
    assert [shortcut_id for shortcut_id, _props in shortcuts] == [SHORTCUT_ID]
    description, trigger = shortcuts[0][1].values()
    assert description == SHORTCUT_DESCRIPTION
    assert trigger == SHORTCUT_TRIGGER
    bind_token = bind_options["handle_token"]
    gio.portal_bus.deliver_response(bind_token, 0, {"shortcuts": GLib.Variant("a(sa{sv})", [(SHORTCUT_ID, {})])})

    # Bound: listens for portal signals on the interface proxy
    signal_handler = portal_proxy.connect.call_args[0][1]
    assert portal_proxy.connect.call_args[0][0] == "g-signal"

    activated_variant = GLib.Variant("(osta{sv})", (SESSION_HANDLE, SHORTCUT_ID, 1000, {}))
    signal_handler(portal_proxy, SENDER, "Activated", activated_variant)
    assert activated == [True]

    # Other sessions/shortcuts must not activate us
    signal_handler(portal_proxy, SENDER, "Activated", GLib.Variant("(osta{sv})", ("/other", SHORTCUT_ID, 1000, {})))
    signal_handler(portal_proxy, SENDER, "Activated", GLib.Variant("(osta{sv})", (SESSION_HANDLE, "other", 1000, {})))
    assert activated == [True]


def test_bind__ignores_rejected_binding(gio: MagicMock, portal_proxy: MagicMock) -> None:
    portal = GlobalShortcutsPortal(lambda: None)
    portal.bind()
    gio.finish_proxy_creation()

    session_call = portal_proxy.call.call_args_list[0]
    token = session_call[0][1].unpack()[0]["handle_token"]
    gio.portal_bus.deliver_response(token, 0, {"session_handle": GLib.Variant("o", SESSION_HANDLE)})

    bind_call = portal_proxy.call.call_args_list[1]
    bind_token = bind_call[0][1].unpack()[3]["handle_token"]
    gio.portal_bus.deliver_response(bind_token, 0, {"shortcuts": GLib.Variant("a(sa{sv})", [])})

    assert portal_proxy.connect.call_args_list == []


def test_bind__proxy_creation_failure_is_swallowed(gio: MagicMock) -> None:
    gio.DBusProxy.new_for_bus_finish.side_effect = GLib.Error("no portal")

    GlobalShortcutsPortal(lambda: None).bind()
    gio.finish_proxy_creation()

    gio.DBusProxy.new_for_bus.return_value.call.assert_not_called()


def test_configure__uses_session_handle(portal_proxy: MagicMock) -> None:
    portal = GlobalShortcutsPortal(lambda: None)
    portal.session_handle = SESSION_HANDLE
    portal._portal = portal_proxy

    assert portal.configure() is True
    configure_call = portal_proxy.call_sync.call_args
    assert configure_call[0][0] == "ConfigureShortcuts"
    assert configure_call[0][1].unpack() == (SESSION_HANDLE, "", {})


def test_configure__fails_without_session() -> None:
    assert GlobalShortcutsPortal(lambda: None).configure() is False


def test_bind__register_failure_does_not_abort_binding(gio: MagicMock, portal_proxy: MagicMock) -> None:
    gio.DBusProxy.new_for_bus_sync.return_value.call_sync.side_effect = GLib.Error("no registry")

    GlobalShortcutsPortal(lambda: None).bind()
    gio.finish_proxy_creation()

    assert portal_proxy.call.call_args_list[0][0][0] == "CreateSession"


def test_bind__response_after_unsubscribe_only(gio: MagicMock, portal_proxy: MagicMock) -> None:
    """The Response subscription is removed once delivered, so a replay can't rebind."""
    portal = GlobalShortcutsPortal(lambda: None)
    portal.bind()
    gio.finish_proxy_creation()

    session_token = portal_proxy.call.call_args_list[0][0][1].unpack()[0]["handle_token"]
    gio.portal_bus.deliver_response(session_token, 0, {"session_handle": GLib.Variant("o", SESSION_HANDLE)})

    assert gio.portal_bus.unsubscribed == [1]
