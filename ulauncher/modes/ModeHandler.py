from __future__ import annotations

from ulauncher.api.result import Result
from ulauncher.api.shared.query import Query
from ulauncher.modes.apps.AppMode import AppMode
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.calc.CalcMode import CalcMode
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode

_modes: list[BaseMode] = []


def get_modes() -> list[BaseMode]:
    global _modes  # noqa: PLW0603
    if not _modes:
        _modes = [FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), AppMode()]
    return _modes


def on_query_change(query: Query) -> bool | list[Result]:
    """
    Iterate over all search modes and run first enabled.
    """
    for mode in get_modes():
        mode.on_query_change(query)

    active_mode = get_mode_from_query(query)
    result = active_mode and active_mode.handle_query(query)
    # TODO(friday): Get rid of this (only used in DeferredResultRenderer.handle_event)
    if isinstance(result, bool):
        return result
    if result:
        return [*result]
    # No mode selected, which means search
    results = search(query)
    # If the search result is empty, add the default items for all other modes (only shortcuts currently)
    if not results and query:
        for mode in get_modes():
            res = mode.get_fallback_results()
            results.extend(res)
    return results


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
