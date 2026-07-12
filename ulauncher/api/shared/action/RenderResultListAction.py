from __future__ import annotations  # noqa: N999

from typing import TYPE_CHECKING

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.internals import effects

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

__all__ = ["RenderResultListAction"]


def RenderResultListAction(results: list[Result], append: bool = False, final: bool = True) -> effects.RenderResults:  # noqa: N802
    warn_legacy_api("RenderResultListAction", "Return a `list[Result]` from your handler instead.")
    return effects.render_results(results, append, final)
