from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api.actions import Action, custom
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning("use `ulauncher.api.actions.custom(data: Any)` instead.")
def ExtensionCustomAction(*args: Any, **kwargs: Any) -> Action[Any]:  # noqa: N802
    """Run custom() to maintain backward compatibility."""
    return custom(*args, **kwargs)
