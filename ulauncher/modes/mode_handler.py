from __future__ import annotations

import logging

from gi.repository import Gdk, Gtk

from ulauncher.internals.result import ActionMessage
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


def handle_action(action_message: ActionMessage | None) -> None:
    if not _handle_action(action_message):
        _events.emit("app:hide_launcher")


def _handle_action(action_message: ActionMessage | None) -> bool:  # noqa: PLR0911, PLR0912
    if action_message is None:
        return False

    event_type = action_message.get("type", "")

    if event_type == "action:do_nothing":
        return True
    if event_type == "action:close_window":
        return False
    if event_type == "action:set_query":
        _events.emit("app:set_query", action_message.get("data", ""))
        return True

    if data := action_message.get("data"):
        if event_type == "action:open":
            open_detached(data)
            return False
        if event_type == "action:clipboard_store":
            clipboard_store(data)
            return False
        if event_type == "action:legacy_run_script" and isinstance(data, list):
            run_script(*data)
            return False
        if event_type == "action:legacy_run_many" and isinstance(data, list):
            keep_open = False
            for action_ in data:
                if _handle_action(action_):
                    keep_open = True
            return keep_open

    if event_type == "action:activate_custom":
        _events.emit("extensions:trigger_event", {"type": "event:activate_custom", "ref": action_message.get("ref")})
        return action_message.get("keep_app_open") is True

    if event_type == "action:launch_trigger":
        _events.emit("extensions:trigger_event", {**action_message, "type": "event:launch_trigger"})
        return True

    _logger.warning("Unknown action type: %s", event_type)
    return False
