from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api.actions import Action, copy
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning("use `ulauncher.api.actions.copy(text: str)` for copying text to the clipboard.")
def CopyToClipboardAction(*args: Any, **kwargs: Any) -> Action[str]:  # noqa: N802
    """Run copy() to maintain backward compatibility."""
    return copy(*args, **kwargs)
