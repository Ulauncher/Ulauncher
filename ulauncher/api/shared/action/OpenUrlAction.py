from __future__ import annotations  # noqa: N999

from ulauncher.api.actions import Action, open  # noqa: A004
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning(
    "use `ulauncher.api.actions.open(text: str)` for opening a file or URL in the default application."
)
def OpenUrlAction(url: str) -> Action[str]:  # noqa: N802
    """Run open() to maintain backward compatibility."""
    return open(url)
