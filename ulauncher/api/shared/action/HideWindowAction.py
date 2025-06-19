from __future__ import annotations  # noqa: N999

from ulauncher.api.warnings import deprecation_warning


@deprecation_warning("set False as the action instead.")
def HideWindowAction() -> bool:  # noqa: N802
    return False
