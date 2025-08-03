from __future__ import annotations

import logging

from gi.repository import Gdk, Gtk

from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.timer import timer

_logger = logging.getLogger()
_events = EventBus("mode")


def clipboard_store(data: str) -> None:
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(data, -1)
    clipboard.store()
    _events.emit("app:toggle_hold", True)
    _events.emit("window:close")
    # Hold the app for 1 second (hopefully enough, 0.25s wasn't) to allow it time to store the clipboard
    # before exiting. There is no gtk3 event or method that works for this unfortunately
    timer(1, lambda: _events.emit("app:toggle_hold", False))


@_events.on
def handle_action(action_metadata: ActionMetadata | None) -> None:
    if not _handle_action(action_metadata):
        _events.emit("window:close")


def _handle_action(action_metadata: ActionMetadata | None) -> bool:  # noqa: PLR0911, PLR0912
    if action_metadata is True:
        return True
    if action_metadata in (False, None):
        return False
    if isinstance(action_metadata, list):
        results = [res if isinstance(res, Result) else Result(**res) for res in action_metadata]
        _events.emit("window:show_results", results)
        return True
    if isinstance(action_metadata, str):
        _events.emit("app:set_query", action_metadata)
        return True

    if isinstance(action_metadata, dict):
        event_type = action_metadata.get("type", "")
        data = action_metadata.get("data")
        if event_type == "action:open" and data:
            open_detached(data)
            return False
        if event_type == "action:clipboard_store" and data:
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
            _events.emit(
                "extension:trigger_event", {"type": "event:activate_custom", "ref": action_metadata.get("ref")}
            )
            return action_metadata.get("keep_app_open") is True

    else:
        _logger.warning("Invalid action from mode: %s", type(action_metadata).__name__)

    return False
