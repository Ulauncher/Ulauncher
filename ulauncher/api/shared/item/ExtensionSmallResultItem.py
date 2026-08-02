from typing import Any  # noqa: N999

from ulauncher.api import Result
from ulauncher.api._deprecation import merge_legacy_positional_args, warn_legacy_api


class ExtensionSmallResultItem(Result):
    compact: bool = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warn_legacy_api("ExtensionSmallResultItem", "Use `ulauncher.api.Result(compact=True)` instead.")
        super().__init__(**merge_legacy_positional_args("ExtensionSmallResultItem", args, kwargs))
