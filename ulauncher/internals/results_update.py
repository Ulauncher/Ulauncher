from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ulauncher.internals.query import Query
    from ulauncher.internals.result import Result


class ResultsUpdate(TypedDict):
    """A self-contained snapshot of what the results view should render.

    Carries everything the view needs so it never has to read back into core state:
    the results, the query they were produced for, and which result to preselect.
    """

    results: list[Result]
    query: Query
    # Name of the result to preselect, or None to fall back to the first.
    selected_name: str | None


def results_update(results: list[Result], query: Query, selected_name: str | None = None) -> ResultsUpdate:
    return {"results": results, "query": query, "selected_name": selected_name}
