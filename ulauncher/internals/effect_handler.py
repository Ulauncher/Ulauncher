from __future__ import annotations

import logging
from typing import cast

from gi.repository import Gdk, Gtk

from ulauncher.internals.effects import EffectMessage, EffectType
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


def handle_effect(effect_msg: EffectMessage) -> None:
    if not _handle_effect(effect_msg):
        _events.emit("app:hide_launcher")


def _handle_effect(effect_msg: EffectMessage) -> bool:  # noqa: PLR0911
    event_type = effect_msg.get("type", "")

    if event_type == EffectType.DO_NOTHING:
        return True
    if event_type == EffectType.CLOSE_WINDOW:
        return False
    if event_type == EffectType.SET_QUERY:
        _events.emit("app:set_query", effect_msg.get("data", ""))
        return True

    if data := effect_msg.get("data"):
        if event_type == EffectType.OPEN:
            open_detached(cast("str", data))
            return False
        if event_type == EffectType.COPY:
            clipboard_store(cast("str", data))
            return False
        if event_type == EffectType.LEGACY_RUN_SCRIPT and isinstance(data, list):
            run_script(*data)
            return False
        if event_type == EffectType.LEGACY_RUN_MANY and isinstance(data, list):
            keep_open = False
            for effect in data:
                assert isinstance(effect, dict)
                if _handle_effect(effect):
                    keep_open = True
            return keep_open

    _logger.warning("Unknown effect type: %s", event_type)
    return False
