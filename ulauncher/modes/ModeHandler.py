from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher.api.result import Result
from ulauncher.api.shared.query import Query
from ulauncher.modes.apps.AppMode import AppMode
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.calc.CalcMode import CalcMode
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.timer import timer

_logger = logging.getLogger()
_events = EventBus("mode")
_modes: list[BaseMode] = []
_triggers: list[Result] = []


def get_modes() -> list[BaseMode]:
    if not _modes:
        _modes.extend([FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), AppMode()])
    return _modes


def on_query_change(query: Query) -> None:
    """
    Iterate over all search modes and run first enabled.
    """
    for mode in get_modes():
        mode.on_query_change(query)

    active_mode = get_mode_from_query(query)
    if active_mode:
        handle_action(active_mode.handle_query(query))
        return
    # No mode selected, which means search
    results = search(query)
    # If the search result is empty, add the default items for all other modes (only shortcuts currently)
    if not results and query:
        for mode in get_modes():
            res = mode.get_fallback_results()
            results.extend(res)
    handle_action(results)


def on_query_backspace(query: Query) -> str | None:
    mode = get_mode_from_query(query)
    return mode.on_query_backspace(query) if mode else None


def get_mode_from_query(query: Query) -> BaseMode | None:
    for mode in get_modes():
        if mode.is_enabled(query):
            return mode
    return None


def refresh_triggers() -> None:
    _triggers.clear()
    for mode in get_modes():
        _triggers.extend([*mode.get_triggers()])


def search(query: Query, min_score: int = 50, limit: int = 50) -> list[Result]:
    # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
    sorted_ = sorted(_triggers, key=lambda i: i.search_score(query), reverse=True)[:limit]
    return list(filter(lambda searchable: searchable.search_score(query) > min_score, sorted_))


@_events.on
def clipboard_store(data: str) -> None:
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(data, -1)
    clipboard.store()
    # hold the app for a bit to make sure it syncs the clipboard before it exists
    # there is no gtk event or function for this unfortunately, but 0.25s should be more than enough
    # 0.02s was enough in my local tests
    _events.emit("app:toggle_hold", True)
    _events.emit("window:close")
    timer(0.25, lambda: _events.emit("app:toggle_hold", False))


@_events.on
def handle_action(action: bool | list[Any] | str | dict[str, Any] | None) -> None:
    if not _handle_action(action):
        _events.emit("window:close")


def _handle_action(action: bool | list[Any] | str | dict[str, Any] | None) -> bool:  # noqa: PLR0911, PLR0912
    if action is True:
        return True
    if action in (False, None):
        return False
    if isinstance(action, list):
        results = [res if isinstance(res, Result) else Result(**res) for res in action]
        _events.emit("window:show_results", results)
        return True
    if isinstance(action, str):
        _events.emit("app:set_query", action)
        return True

    if isinstance(action, dict):
        event_type = action.get("type", "")
        data = action.get("data")
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
            for action in data:
                if _handle_action(action):
                    keep_open = True
            return keep_open
        if event_type == "action:activate_custom":
            _events.emit("extension:trigger_event", {"type": "event:activate_custom", "ref": action.get("ref")})
            return action.get("keep_app_open") is True

    else:
        _logger.warning("Invalid action from mode: %s", type(action).__name__)

    return False
