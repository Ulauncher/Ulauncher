from __future__ import annotations

from typing import Any

from ulauncher.api.extension import Extension
from ulauncher.internals import effects
from ulauncher.internals.result import Result as _Result

__all__ = ["Extension", "ExtensionResult", "ExtensionSmallResult", "Result", "effects"]


class Result(_Result):
    """
    :param on_enter: The effect to be performed when the result is activated (legacy: please use `actions` instead).
                     Should be a return value of the `ExtensionCustomAction` function.
    :param on_alt_enter: The effect to be performed when the result is activated with the Alt key pressed
                         (legacy: please use `actions` instead).
    """

    # Declared as the input type, not the stored one: __setitem__ converts on the way in, and the
    # app reads these back off the dict rather than through the attribute.
    #: Superseded by `actions`, which takes precedence when both are set. Kept for the v2 extension API.
    on_enter: effects.EffectMessageInput | None = None
    on_alt_enter: effects.EffectMessageInput | None = None

    def __setitem__(self, key: str, value: Any) -> None:
        if value is None:
            # v2 extensions pass None for fields they didn't compute, expecting the class default.
            return

        if key in ["on_enter", "on_alt_enter"]:
            from ulauncher.api._deprecation import warn_legacy_api
            from ulauncher.api._utils import convert_to_effect_message

            warn_legacy_api(key, "Use the `actions` parameter instead.")
            value = convert_to_effect_message(value)

        super().__setitem__(key, value)


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
