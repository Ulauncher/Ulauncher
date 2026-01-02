from __future__ import annotations

from ulauncher.internals.result import Result


class ShortcutResult(Result):
    is_default_search = False
    cmd = ""
    actions = {"run": {"name": "Run shortcut", "icon": "system-run"}}


class ShortcutStaticTrigger(Result):
    searchable = True
    cmd = ""
    actions = {"run_static": {"name": "Run shortcut", "icon": "system-run"}}


class StaticShortcutResult(ShortcutResult):
    actions = {"run_static": {"name": "Run shortcut", "icon": "system-run"}}
