from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects

__all__ = ["DoNothingAction"]


def DoNothingAction() -> effects.DoNothing:  # noqa: N802
    warn_legacy_api("DoNothingAction", "Use `ulauncher.api.effects.do_nothing()` instead.")
    return effects.do_nothing()
