from __future__ import annotations

import logging
from typing import cast

from gi.repository import Gdk, Gtk

from ulauncher.internals.actions import ActionMessage, ActionType
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.timer import timer

_logger = logging.getLogger()
_events = EventBus()


def clipboard_store(data: str) -> None:
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(data, -1)
    clipboard.store()
    _events.emit("app:toggle_hold", True)
    _events.emit("app:hide_launcher")
    # Hold the app for 1 second (hopefully enough, 0.25s wasn't) to allow it time to store the clipboard
    # before exiting. There is no gtk3 event or method that works for this unfortunately
    timer(1, lambda: _events.emit("app:toggle_hold", False))


def handle_action(action_msg: ActionMessage | None) -> None:
    if not _handle_action(action_msg):
        _events.emit("app:hide_launcher")


def _handle_action(action_msg: ActionMessage | None) -> bool:  # noqa: PLR0911
    if action_msg is None:
        return False

    event_type = action_msg.get("type", "")

    if event_type == ActionType.DO_NOTHING:
        return True
    if event_type == ActionType.CLOSE_WINDOW:
        return False
    if event_type == ActionType.SET_QUERY:
        _events.emit("app:set_query", action_msg.get("data", ""))
        return True

    if data := action_msg.get("data"):
        if event_type == ActionType.OPEN:
            open_detached(cast("str", data))
            return False
        if event_type == ActionType.COPY:
            clipboard_store(cast("str", data))
            return False
        if event_type == ActionType.LEGACY_RUN_SCRIPT and isinstance(data, list):
            run_script(*data)
            return False
        if event_type == ActionType.LEGACY_RUN_MANY and isinstance(data, list):
            keep_open = False
            for action_ in data:
                assert isinstance(action_, dict)
                if _handle_action(action_):
                    keep_open = True
            return keep_open

    _logger.warning("Unknown action type: %s", event_type)
    return False
