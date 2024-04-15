from __future__ import annotations

import logging
import subprocess
from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher.api.result import Result
from ulauncher.api.shared.query import Query
from ulauncher.modes.apps.AppMode import AppMode
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.calc.CalcMode import CalcMode
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.extensions.ExtensionSocketServer import ExtensionSocketServer
from ulauncher.modes.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.Settings import Settings

_logger = logging.getLogger()
_events = EventBus("mode")
_modes: list[BaseMode] = []


def get_modes() -> list[BaseMode]:
    global _modes  # noqa: PLW0603
    if not _modes:
        _modes = [FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), AppMode()]
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


def search(query: Query, min_score: int = 50, limit: int = 50) -> list[Result]:
    searchables: list[Result] = []
    for mode in get_modes():
        searchables.extend([*mode.get_triggers()])

    # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
    sorted_ = sorted(searchables, key=lambda i: i.search_score(query), reverse=True)[:limit]
    return list(filter(lambda searchable: searchable.search_score(query) > min_score, sorted_))


@_events.on
def clipboard_store(data: str) -> None:
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(data, -1)
    clipboard.store()
    _events.emit("window:hide")
    copy_hook = Settings.load().copy_hook
    if copy_hook:
        _logger.info("Running copy hook: %s", copy_hook)
        subprocess.Popen(["sh", "-c", copy_hook])


@_events.on
def handle_action(event: bool | list[Any] | str | dict[str, Any] | None) -> None:
    if isinstance(event, list):
        results = [res if isinstance(res, Result) else Result(**res) for res in event]
        _events.emit("window:show_results", results)
    elif isinstance(event, str):
        _events.emit("app:set_query", event)
    elif event in (None, False) or (isinstance(event, dict) and not _handle_action(event)):
        _events.emit("window:hide")


def _handle_action(event: dict[str, Any]) -> bool:
    event_type = event.get("type", "")
    data = event.get("data")
    ext_id = event.get("ext_id")
    controller = None
    if event_type == "action:open" and data:
        open_detached(data)
    elif event_type == "action:clipboard_store" and data:
        clipboard_store(data)

    elif event_type == "action:legacy_run_script" and isinstance(data, list):
        run_script(*data)
    elif event_type == "action:legacy_run_many" and isinstance(data, list):
        keep_open = False
        for action in data:
            if _handle_action(action):
                keep_open = True
        return keep_open
    elif event_type == "event:activate_custom":
        _events.emit("extension:trigger_event", event)
    elif event_type.startswith("event") and ext_id:
        controller = ExtensionSocketServer().get_controller_by_id(ext_id)
        if controller:
            controller.trigger_event(event)
            return True

    else:
        _logger.warning("Invalid result from mode: %s", type(event).__name__)

    return False
