from __future__ import annotations  # noqa: N999

from ulauncher.api.warnings import deprecation_warning


@deprecation_warning("set True as the action instead")
def DoNothingAction() -> bool:  # noqa: N802
    return True
