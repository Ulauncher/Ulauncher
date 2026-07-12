from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects

__all__ = ["HideWindowAction"]


def HideWindowAction() -> effects.CloseWindow:  # noqa: N802
    warn_legacy_api("HideWindowAction", "Use `ulauncher.api.effects.close_window()` instead.")
    return effects.close_window()
