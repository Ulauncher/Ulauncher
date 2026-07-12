from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects

__all__ = ["OpenAction"]


def OpenAction(item: str) -> effects.Open:  # noqa: N802
    warn_legacy_api("OpenAction", "Use `ulauncher.api.effects.open(path)` instead.")
    return effects.open(item)
