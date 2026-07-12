from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects

__all__ = ["OpenUrlAction"]


def OpenUrlAction(url: str) -> effects.Open:  # noqa: N802
    warn_legacy_api("OpenUrlAction", "Use `ulauncher.api.effects.open(url)` instead.")
    return effects.open(url)
