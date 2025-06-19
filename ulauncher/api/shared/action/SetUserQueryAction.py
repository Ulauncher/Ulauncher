from __future__ import annotations  # noqa: N999

from ulauncher.api.actions import Action, set_query
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning("use `ulauncher.api.actions.set_query(query: str)` instead.")
def SetUserQueryAction(new_query: str) -> Action[str]:  # noqa: N802
    """Run set_query() to maintain backward compatibility."""
    return set_query(new_query)
