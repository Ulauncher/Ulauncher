from __future__ import annotations

from ulauncher.internals.result import Result


class ShortcutResult(Result):
    is_default_search = False
    run_without_argument = False
    cmd = ""


class ShortcutStaticTrigger(Result):
    searchable = True
    run_without_argument = False
    cmd = ""
