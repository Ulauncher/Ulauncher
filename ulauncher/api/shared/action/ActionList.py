from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api.actions import Action, action_list
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning(
    "use `ulauncher.api.actions.custom(data: Any)` to receive an event when result is selected "
    "then return a list of new result items there."
)
def ActionList(*args: Any, **kwargs: Any) -> Action[list[Any]]:  # noqa: N802
    """Run action_list() to maintain backward compatibility."""
    return action_list(*args, **kwargs)
