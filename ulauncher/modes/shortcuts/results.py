from __future__ import annotations

from ulauncher.internals.result import Result


class ShortcutResult(Result):
    is_default_search: bool = False
    run_without_argument: bool = False
    cmd: str = ""
    actions = {"run": {"name": "Run shortcut", "icon": "system-run"}}


class ShortcutStaticTrigger(Result):
    searchable: bool = True
    run_without_argument: bool = False
    cmd: str = ""
    actions = {"run_static": {"name": "Run shortcut", "icon": "system-run"}}


class StaticShortcutResult(ShortcutResult):
    actions = {"run_static": {"name": "Run shortcut", "icon": "system-run"}}
