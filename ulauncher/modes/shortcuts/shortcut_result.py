from __future__ import annotations

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class ShortcutResult(Result):
    searchable = True
    is_default_search = False
    run_without_argument = False
    cmd = ""

    def get_highlightable_input(self, query: Query) -> str | None:
        return str(query) if self.keyword != query.keyword else None
