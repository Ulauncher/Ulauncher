from __future__ import annotations  # noqa: N999

from ulauncher.api.warnings import deprecation_warning
from ulauncher.internals.result import Result


@deprecation_warning(
    "use `ulauncher.api.actions.custom(data: Any)` then handle it in `on_item_enter` by returning `list[Result]."
)
def RenderResultListAction(results: list[Result]) -> list[Result]:  # noqa: N802
    # TODO: Remove the possibility of passing result items as actions in v7
    return results
