from __future__ import annotations

from Xlib import X
from Xlib.display import Display
from Xlib.protocol.event import ClientMessage
from Xlib.xobject.drawable import Window

_EWMH_SOURCE_APPLICATION = 1


def get_client_windows_top_first(display: Display) -> list[Window]:
    root = display.screen().root
    prop = root.get_full_property(display.get_atom("_NET_CLIENT_LIST_STACKING"), X.AnyPropertyType)
    if not prop:
        return []
    return [display.create_resource_object("window", win_id) for win_id in reversed(prop.value) if win_id]


def activate_window(display: Display, window: Window) -> None:
    event = ClientMessage(
        window=window,
        client_type=display.get_atom("_NET_ACTIVE_WINDOW"),
        data=(32, [_EWMH_SOURCE_APPLICATION, X.CurrentTime, window.id, 0, 0]),
    )
    display.screen().root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    display.flush()
