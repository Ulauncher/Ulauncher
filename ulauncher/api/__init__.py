from typing import Any

from ulauncher.api.extension import Extension
from ulauncher.internals import effects
from ulauncher.internals.result import Result as _Result

__all__ = ["Extension", "ExtensionResult", "ExtensionSmallResult", "Result", "effects"]


class Result(_Result):
    def __setitem__(self, key: str, value: Any) -> None:
        if key in ["on_enter", "on_alt_enter"] and value is not None:
            from ulauncher.api._deprecation import warn_legacy_api
            from ulauncher.internals import effect_utils

            warn_legacy_api(key, "Use the `actions` parameter instead.")
            value = effect_utils.convert_to_effect_message(value)

        super().__setitem__(key, value)


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
